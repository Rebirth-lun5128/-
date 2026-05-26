from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from auth import require_merchant
from database import get_db
from models.user import User
from models.store import Store
from models.order import CombinedOrder, SubOrder, SubOrderTimeline, OrderModification
from schemas.order import SubOrderOut, SubOrderDetailOut, SubOrderItemOut, SubOrderTimelineOut, ModificationOut
from websocket import manager

router = APIRouter(prefix="/api/merchant/orders", tags=["商家端-订单"])


def _get_store(user: User, db: Session) -> Store:
    s = db.query(Store).filter(Store.user_id == user.id).first()
    if not s:
        raise HTTPException(status_code=404, detail="请先入驻")
    return s


def _add_sub_timeline(sub_order_id: int, status: str, description: str, db: Session):
    db.add(SubOrderTimeline(sub_order_id=sub_order_id, status=status, description=description))


def _sub_order_summary(sub) -> dict:
    return {
        "sub_order_id": sub.id, "combined_order_id": sub.combined_order_id,
        "order_no": sub.combined_order.order_no if sub.combined_order else "",
        "status": sub.status, "store_id": sub.store_id,
        "items_total": float(sub.items_total),
        "store_name": sub.store_name_snapshot,
    }


class SubOrderListOut:
    """简单的子单列表输出"""
    total: int
    items: list


@router.get("")
def list_orders(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    status: str = Query(default=""),
    user: User = Depends(require_merchant),
    db: Session = Depends(get_db),
):
    store = _get_store(user, db)
    query = db.query(SubOrder).filter(SubOrder.store_id == store.id)
    if status:
        query = query.filter(SubOrder.status == status)

    total = query.count()
    items = query.order_by(SubOrder.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    result_items = []
    for sub in items:
        so = SubOrderOut.model_validate(sub)
        so.store_name = sub.store_name_snapshot or store.name
        d = so.model_dump()
        d["order_no"] = sub.combined_order.order_no if sub.combined_order else ""
        d["address_snapshot"] = sub.combined_order.address_snapshot if sub.combined_order else {}
        result_items.append(d)

    return {"total": total, "items": result_items}


@router.get("/{sub_id}")
def get_order(sub_id: int, user: User = Depends(require_merchant), db: Session = Depends(get_db)):
    store = _get_store(user, db)
    sub = db.query(SubOrder).filter(SubOrder.id == sub_id, SubOrder.store_id == store.id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="订单不存在")

    result = SubOrderDetailOut.model_validate(sub)
    result.store_name = sub.store_name_snapshot or store.name
    result.items = [SubOrderItemOut.model_validate(i) for i in (sub.items or [])]
    result.timeline = [
        SubOrderTimelineOut.model_validate(t)
        for t in (sub.timeline.order_by(SubOrderTimeline.created_at.asc()).all() if sub.timeline else [])
    ]
    data = result.model_dump()
    if sub.combined_order:
        data["order_no"] = sub.combined_order.order_no
        data["address_snapshot"] = sub.combined_order.address_snapshot
    return data


@router.put("/{sub_id}/accept")
def accept_order(sub_id: int, user: User = Depends(require_merchant), db: Session = Depends(get_db)):
    store = _get_store(user, db)
    sub = db.query(SubOrder).filter(SubOrder.id == sub_id, SubOrder.store_id == store.id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="订单不存在")
    if sub.status != "pending_accept":
        raise HTTPException(status_code=400, detail="当前状态不可接单")

    sub.status = "preparing"
    sub.accepted_at = datetime.now()
    _add_sub_timeline(sub.id, "preparing", "商家已接单，正在准备餐品", db)
    db.commit()
    db.refresh(sub)
    order = sub.combined_order
    manager.push_order_event_sync("order_accepted", _sub_order_summary(sub), user_id=order.user_id if order else None)
    result = SubOrderOut.model_validate(sub)
    result.store_name = store.name
    return result


@router.put("/{sub_id}/reject")
def reject_order(
    sub_id: int,
    reason: str = Query(default=""),
    user: User = Depends(require_merchant),
    db: Session = Depends(get_db),
):
    store = _get_store(user, db)
    sub = db.query(SubOrder).filter(SubOrder.id == sub_id, SubOrder.store_id == store.id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="订单不存在")
    if sub.status != "pending_accept":
        raise HTTPException(status_code=400, detail="当前状态不可拒单")

    sub.status = "cancelled"
    sub.cancel_reason = reason or "商家拒单"
    sub.cancel_by = "merchant"
    _add_sub_timeline(sub.id, "cancelled", f"商家拒单: {reason or '暂无法接单'}", db)

    # 更新总单状态
    order = sub.combined_order
    if order:
        statuses = [s.status for s in order.sub_orders]
        if all(s == "cancelled" for s in statuses):
            order.status = "cancelled"
        elif all(s in ("completed", "cancelled") for s in statuses):
            order.status = "completed" if all(s == "completed" for s in statuses) else "partial"

    db.commit()
    db.refresh(sub)
    if order:
        manager.push_order_event_sync("order_rejected", _sub_order_summary(sub), user_id=order.user_id)
    result = SubOrderOut.model_validate(sub)
    result.store_name = store.name
    return result


@router.put("/{sub_id}/ready")
def mark_ready(sub_id: int, user: User = Depends(require_merchant), db: Session = Depends(get_db)):
    store = _get_store(user, db)
    sub = db.query(SubOrder).filter(SubOrder.id == sub_id, SubOrder.store_id == store.id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="订单不存在")
    if sub.status != "preparing":
        raise HTTPException(status_code=400, detail="当前状态不可出餐")

    sub.status = "ready"
    sub.ready_at = datetime.now()
    _add_sub_timeline(sub.id, "ready", "餐品已备好，等待骑手取餐", db)
    db.commit()
    db.refresh(sub)

    order = sub.combined_order
    if order:
        manager.push_order_event_sync("order_ready", _sub_order_summary(sub), user_id=order.user_id)
        # 所有未取消子单都 ready 时广播给骑手
        non_cancelled = [s for s in order.sub_orders if s.status != "cancelled"]
        if all(s.status == "ready" for s in non_cancelled):
            manager.push_order_event_sync(
                "new_delivery",
                {"combined_order_id": order.id, "order_no": order.order_no,
                 "store_count": len(non_cancelled),
                 "items_total": float(order.items_total)},
                broadcast_role="rider",
            )

    result = SubOrderOut.model_validate(sub)
    result.store_name = store.name
    return result


# ---- 订单修改审核 ----
@router.get("/modifications")
def list_modifications(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    status: str = Query(default=""),
    user: User = Depends(require_merchant),
    db: Session = Depends(get_db),
):
    """查看与本店铺相关的修改申请"""
    store = _get_store(user, db)
    sub_ids = db.query(SubOrder.id).filter(SubOrder.store_id == store.id).all()
    sub_id_list = [s[0] for s in sub_ids]
    if not sub_id_list:
        return {"total": 0, "items": []}

    query = db.query(OrderModification).filter(
        OrderModification.sub_order_id.in_(sub_id_list)
    )
    if status:
        query = query.filter(OrderModification.status == status)

    total = query.count()
    items = query.order_by(OrderModification.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    results = []
    for m in items:
        r = ModificationOut.model_validate(m)
        order = db.query(CombinedOrder).filter(CombinedOrder.id == m.combined_order_id).first()
        r.order_no = order.order_no if order else ""
        r.store_name = store.name
        if m.sub_order_id:
            sub = db.query(SubOrder).filter(SubOrder.id == m.sub_order_id).first()
            r.items_total = float(sub.items_total) if sub else 0
        results.append(r)

    return {"total": total, "items": results}


@router.put("/modifications/{mod_id}/approve", response_model=ModificationOut)
def approve_modification(
    mod_id: int,
    comment: str = Query(default=""),
    user: User = Depends(require_merchant),
    db: Session = Depends(get_db),
):
    """商家同意修改申请"""
    store = _get_store(user, db)
    mod = db.query(OrderModification).filter(OrderModification.id == mod_id).first()
    if not mod:
        raise HTTPException(status_code=404, detail="申请不存在")
    if mod.status != "pending_review":
        raise HTTPException(status_code=400, detail="申请已处理")

    if mod.sub_order_id:
        sub = db.query(SubOrder).filter(SubOrder.id == mod.sub_order_id, SubOrder.store_id == store.id).first()
        if not sub:
            raise HTTPException(status_code=404, detail="无权限处理该申请")

    mod.status = "approved"
    mod.reviewed_by = user.id
    mod.review_comment = comment
    mod.reviewed_at = datetime.now()

    if mod.type in ("cancel", "refund") and mod.sub_order_id:
        sub = db.query(SubOrder).filter(SubOrder.id == mod.sub_order_id).first()
        if sub:
            sub.status = "cancelled"
            sub.cancel_reason = mod.reason or "用户申请退单(商家同意)"
            sub.cancel_by = "user"
            _add_sub_timeline(sub.id, "cancelled", f"商家同意退单: {mod.reason}", db)
            order = sub.combined_order
            if order:
                statuses = [s.status for s in order.sub_orders]
                if all(s == "cancelled" for s in statuses):
                    order.status = "cancelled"
                elif all(s in ("completed", "cancelled") for s in statuses):
                    order.status = "completed" if all(s == "completed" for s in statuses) else "partial"
    elif mod.type == "address_change":
        order = db.query(CombinedOrder).filter(CombinedOrder.id == mod.combined_order_id).first()
        if order and mod.new_address:
            order.address_snapshot = mod.new_address
            if mod.sub_order_id:
                sub = db.query(SubOrder).filter(SubOrder.id == mod.sub_order_id).first()
                if sub:
                    _add_sub_timeline(sub.id, "address_changed", "用户修改收货地址(商家同意)", db)

    db.commit()
    db.refresh(mod)

    order = db.query(CombinedOrder).filter(CombinedOrder.id == mod.combined_order_id).first()
    if order:
        manager.push_order_event_sync(
            "modification_approved",
            {"modification_id": mod.id, "type": mod.type, "status": "approved"},
            user_id=order.user_id,
        )

    result = ModificationOut.model_validate(mod)
    result.order_no = order.order_no if order else ""
    result.store_name = store.name
    return result


@router.put("/modifications/{mod_id}/reject", response_model=ModificationOut)
def reject_modification(
    mod_id: int,
    comment: str = Query(default=""),
    user: User = Depends(require_merchant),
    db: Session = Depends(get_db),
):
    """商家拒绝修改申请"""
    store = _get_store(user, db)
    mod = db.query(OrderModification).filter(OrderModification.id == mod_id).first()
    if not mod:
        raise HTTPException(status_code=404, detail="申请不存在")
    if mod.status != "pending_review":
        raise HTTPException(status_code=400, detail="申请已处理")

    if mod.sub_order_id:
        sub = db.query(SubOrder).filter(SubOrder.id == mod.sub_order_id, SubOrder.store_id == store.id).first()
        if not sub:
            raise HTTPException(status_code=404, detail="无权限处理该申请")

    mod.status = "rejected"
    mod.reviewed_by = user.id
    mod.review_comment = comment
    mod.reviewed_at = datetime.now()

    if mod.sub_order_id:
        _add_sub_timeline(mod.sub_order_id, "mod_rejected", f"商家拒绝申请: {comment or '不同意'}")

    db.commit()
    db.refresh(mod)

    order = db.query(CombinedOrder).filter(CombinedOrder.id == mod.combined_order_id).first()
    if order:
        manager.push_order_event_sync(
            "modification_rejected",
            {"modification_id": mod.id, "type": mod.type, "status": "rejected"},
            user_id=order.user_id,
        )

    result = ModificationOut.model_validate(mod)
    result.order_no = order.order_no if order else ""
    result.store_name = store.name
    return result
