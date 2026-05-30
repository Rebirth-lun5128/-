"""管理后台 — 分区管理员内置配送模式"""
import json
from datetime import datetime, date

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from sqlalchemy import func

from auth import require_any_admin
from database import get_db
from models.user import User
from models.rider import Rider
from models.order import CombinedOrder, SubOrder, SubOrderTimeline
from models.region import Settlement, SystemConfig
from schemas.order import CombinedOrderOut, SubOrderOut
from websocket import manager

router = APIRouter(prefix="/api/admin/delivery", tags=["管理后台-内置配送"])


def _get_or_create_rider(user: User, db: Session) -> Rider:
    """获取或创建管理员的骑手记录"""
    rider = db.query(Rider).filter(Rider.user_id == user.id).first()
    if not rider:
        if user.role not in ("district_admin", "super_admin"):
            raise HTTPException(status_code=403, detail="仅分区管理员可使用配送模式")
        # 超级管理员不强制要求 district_id
        if user.role != "super_admin" and not user.district_id:
            raise HTTPException(status_code=400, detail="请先分配管理分区")
        rider = Rider(
            user_id=user.id,
            real_name=user.nickname or "管理员配送",
            phone=user.phone,
            district_id=user.district_id if user.role == "district_admin" else None,
            audit_status="approved",
            status="offline",
        )
        db.add(rider)
        db.commit()
        db.refresh(rider)
    return rider


# ==================== 切换配送模式 ====================

@router.get("/status")
def delivery_status(user: User = Depends(require_any_admin), db: Session = Depends(get_db)):
    """获取当前配送模式状态"""
    rider = db.query(Rider).filter(Rider.user_id == user.id).first()
    if not rider:
        return {"mode": "inactive", "rider_status": None, "active_order": None}

    active_order = None
    if rider.status == "busy":
        order = db.query(CombinedOrder).filter(
            CombinedOrder.rider_id == rider.id,
            CombinedOrder.status == "delivering",
        ).first()
        if order:
            active_order = {
                "id": order.id, "order_no": order.order_no,
                "total_price": float(order.total_price),
                "store_count": len([s for s in (order.sub_orders or []) if s.status != "cancelled"]),
            }

    return {
        "mode": "active" if rider.status != "offline" else "standby",
        "rider_status": rider.status,
        "active_order": active_order,
    }


@router.put("/toggle")
def toggle_delivery(
    enable: bool = Query(...),
    user: User = Depends(require_any_admin),
    db: Session = Depends(get_db),
):
    """开启/关闭配送模式"""
    rider = _get_or_create_rider(user, db)

    if enable:
        if rider.audit_status != "approved":
            rider.audit_status = "approved"  # 管理员自动通过
        rider.status = "online"
        msg = "配送模式已开启，可以接收订单"
    else:
        if rider.status == "busy":
            raise HTTPException(status_code=400, detail="当前有进行中的配送，请先完成后再关闭")
        rider.status = "offline"
        msg = "配送模式已关闭"

    db.commit()
    return {"message": msg, "rider_status": rider.status}


# ==================== 待接订单 ====================

@router.get("/pending")
def pending_orders(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    user: User = Depends(require_any_admin),
    db: Session = Depends(get_db),
):
    """获取本分区待配送订单（所有子单 ready 的总单）"""
    rider = _get_or_create_rider(user, db)
    if rider.status == "offline":
        return {"total": 0, "items": [], "hint": "请先开启配送模式"}

    district_filter = []
    if rider.district_id:
        district_filter = [CombinedOrder.district_id == rider.district_id]
    candidates = db.query(CombinedOrder).filter(
        CombinedOrder.status == "pending",
        *district_filter,
    ).all()

    ready_orders = []
    for order in candidates:
        non_cancelled = [s for s in order.sub_orders if s.status != "cancelled"]
        if non_cancelled and all(s.status == "ready" for s in non_cancelled):
            ready_orders.append(order)

    total = len(ready_orders)
    ready_orders.sort(key=lambda o: o.created_at or datetime.min)
    paged = ready_orders[(page - 1) * page_size: page * page_size]

    items = []
    for order in paged:
        o = CombinedOrderOut.model_validate(order)
        o.sub_orders = [SubOrderOut.model_validate(s) for s in (order.sub_orders or [])]
        for so in o.sub_orders:
            so.store_name = so.store_name_snapshot
        items.append(o.model_dump())

    return {"total": total, "items": items}


# ==================== 接单 / 送达 ====================

@router.put("/orders/{order_id}/accept")
def accept_order(order_id: int, user: User = Depends(require_any_admin), db: Session = Depends(get_db)):
    """接单"""
    rider = _get_or_create_rider(user, db)
    if rider.status == "offline":
        raise HTTPException(status_code=400, detail="请先开启配送模式")

    order = db.query(CombinedOrder).filter(CombinedOrder.id == order_id).with_for_update().first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status != "pending":
        raise HTTPException(status_code=400, detail="该订单已被其他人接单")
    if rider.district_id and order.district_id != rider.district_id:
        raise HTTPException(status_code=400, detail="该订单不在你的配送区域")

    order.rider_id = rider.id
    order.status = "delivering"
    order.picked_at = datetime.now()
    rider.status = "busy"

    for sub in order.sub_orders:
        if sub.status == "cancelled":
            continue
        sub.status = "delivering"
        db.add(SubOrderTimeline(sub_order_id=sub.id, status="delivering",
                                description=f"管理员 {rider.real_name} 已取餐配送"))

    db.commit()
    db.refresh(order)

    # WebSocket 推送
    merchant_ids = {sub.store.user_id for sub in order.sub_orders if sub.store and sub.status != "cancelled"}
    summary = {
        "id": order.id, "order_no": order.order_no, "status": order.status,
        "total_price": float(order.total_price),
        "store_count": len([s for s in (order.sub_orders or []) if s.status != "cancelled"]),
        "rider_name": rider.real_name,
    }
    manager.push_order_event_sync("rider_accepted", summary, user_id=order.user_id)
    for mid in merchant_ids:
        manager.push_order_event_sync("rider_accepted", summary, merchant_user_id=mid)

    if rider.lat is not None and rider.lng is not None:
        manager.push_order_event_sync(
            "rider_location",
            {"order_id": order.id, "rider_id": rider.id, "rider_name": rider.real_name,
             "lat": float(rider.lat), "lng": float(rider.lng)},
            user_id=order.user_id,
        )

    result = CombinedOrderOut.model_validate(order)
    result.sub_orders = [SubOrderOut.model_validate(s) for s in (order.sub_orders or [])]
    for so in result.sub_orders:
        so.store_name = so.store_name_snapshot
    return result.model_dump()


@router.put("/orders/{order_id}/deliver")
def mark_delivered(order_id: int, user: User = Depends(require_any_admin), db: Session = Depends(get_db)):
    """确认送达"""
    rider = _get_or_create_rider(user, db)

    order = db.query(CombinedOrder).filter(
        CombinedOrder.id == order_id, CombinedOrder.rider_id == rider.id
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status != "delivering":
        raise HTTPException(status_code=400, detail="当前状态不可确认送达")

    rider_cfg = db.query(SystemConfig).filter(SystemConfig.config_key == "rider_per_order").first()
    rider_earning = float(rider_cfg.config_value) if rider_cfg else 5.0

    period = datetime.now().strftime("%Y-%m")
    order.status = "completed"
    order.delivered_at = datetime.now()
    order.completed_at = datetime.now()
    rider.status = "online"
    rider.total_orders = (rider.total_orders or 0) + 1
    rider.balance = float(rider.balance or 0) + rider_earning

    for sub in order.sub_orders:
        if sub.status == "cancelled":
            continue
        sub.status = "completed"
        items_total = float(sub.items_total)

        # 阶梯佣金计算
        rate = float(sub.commission_rate)
        district_rate = 0.0
        try:
            monthly_sales = db.query(func.coalesce(func.sum(SubOrder.items_total), 0)).filter(
                SubOrder.store_id == sub.store_id,
                SubOrder.status == "completed",
                func.strftime('%Y-%m', SubOrder.updated_at) == func.strftime('%Y-%m', 'now'),
            ).scalar() or 0
            ct_cfg = db.query(SystemConfig).filter(SystemConfig.config_key == "commission_tiers").first()
            if ct_cfg:
                tiers = json.loads(ct_cfg.config_value) if ct_cfg.config_value else []
                for t in tiers:
                    t_min = float(t.get("min", 0))
                    t_max = float(t.get("max", -1))
                    if monthly_sales >= t_min and (t_max < 0 or monthly_sales < t_max):
                        rate = float(t.get("rate", 0))
                        break
            dct_cfg = db.query(SystemConfig).filter(SystemConfig.config_key == "district_commission_tiers").first()
            if dct_cfg:
                dtiers = json.loads(dct_cfg.config_value) if dct_cfg.config_value else []
                for t in dtiers:
                    t_min = float(t.get("min", 0))
                    t_max = float(t.get("max", -1))
                    if monthly_sales >= t_min and (t_max < 0 or monthly_sales < t_max):
                        district_rate = float(t.get("rate", 0))
                        break
        except Exception:
            pass

        platform_fee = round(items_total * rate, 2)
        district_fee = round(items_total * district_rate, 2)
        merchant_net = round(items_total - platform_fee - district_fee, 2)

        store_district_id = sub.store.district_id if sub.store else None
        db.add(Settlement(
            target_type="store", target_id=sub.store_id,
            amount=items_total, fee=platform_fee, net_amount=merchant_net,
            district_fee=district_fee, district_id=store_district_id,
            period=period, status="pending",
        ))
        db.add(SubOrderTimeline(
            sub_order_id=sub.id, status="completed",
            description=f"管理员已送达 | 商品¥{items_total:.2f} 平台扣¥{platform_fee:.2f}"
            + (f" 分区扣¥{district_fee:.2f}" if district_fee > 0 else "")
            + f" 商家得¥{merchant_net:.2f}",
        ))

    if any(s.status == "cancelled" for s in order.sub_orders):
        order.status = "partial"

    db.commit()

    merchant_ids = {sub.store.user_id for sub in order.sub_orders if sub.store and sub.status != "cancelled"}
    summary = {
        "id": order.id, "order_no": order.order_no, "status": order.status,
        "total_price": float(order.total_price),
        "store_count": len([s for s in (order.sub_orders or []) if s.status != "cancelled"]),
        "rider_name": rider.real_name,
    }
    manager.push_order_event_sync("order_delivered", summary, user_id=order.user_id)
    for mid in merchant_ids:
        manager.push_order_event_sync("order_delivered", summary, merchant_user_id=mid)

    return {"message": "已确认送达", "earning": rider_earning}


# ==================== 我的配送记录 ====================

@router.get("/my-orders")
def my_delivery_orders(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    user: User = Depends(require_any_admin),
    db: Session = Depends(get_db),
):
    """查看自己的配送记录"""
    rider = db.query(Rider).filter(Rider.user_id == user.id).first()
    if not rider:
        return {"total": 0, "items": []}

    query = db.query(CombinedOrder).filter(CombinedOrder.rider_id == rider.id)
    total = query.count()
    orders = query.order_by(CombinedOrder.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    items = []
    for order in orders:
        o = CombinedOrderOut.model_validate(order)
        o.sub_orders = [SubOrderOut.model_validate(s) for s in (order.sub_orders or [])]
        for so in o.sub_orders:
            so.store_name = so.store_name_snapshot
        items.append(o.model_dump())

    return {"total": total, "items": items}


@router.get("/wallet")
def delivery_wallet(user: User = Depends(require_any_admin), db: Session = Depends(get_db)):
    """配送收入概览"""
    rider = db.query(Rider).filter(Rider.user_id == user.id).first()
    if not rider:
        return {"balance": 0, "total_orders": 0, "today_income": 0}

    today = date.today()
    today_count = db.query(func.count(CombinedOrder.id)).filter(
        CombinedOrder.rider_id == rider.id,
        CombinedOrder.status.in_(["completed", "partial"]),
        func.date(CombinedOrder.completed_at) == today,
    ).scalar() or 0

    rider_cfg = db.query(SystemConfig).filter(SystemConfig.config_key == "rider_per_order").first()
    per_order = float(rider_cfg.config_value) if rider_cfg else 5.0

    return {
        "balance": float(rider.balance or 0),
        "total_orders": rider.total_orders or 0,
        "today_income": today_count * per_order,
        "per_order": per_order,
    }


# ==================== 提现 ====================

@router.post("/withdraw")
def request_withdrawal(
    amount: float = Body(..., gt=0),
    user: User = Depends(require_any_admin),
    db: Session = Depends(get_db),
):
    """申请提现配送收入"""
    rider = _get_or_create_rider(user, db)
    balance = float(rider.balance or 0)
    if amount > balance:
        raise HTTPException(status_code=400, detail=f"余额不足，当前可提现 ¥{balance:.2f}")
    if amount < 10:
        raise HTTPException(status_code=400, detail="最低提现金额 ¥10")

    period = datetime.now().strftime("%Y-%m")
    settlement = Settlement(
        target_type="rider",
        target_id=rider.id,
        amount=amount,
        net_amount=amount,  # 骑手提现无手续费
        fee=0,
        period=period,
        status="pending",
    )
    db.add(settlement)
    db.commit()
    db.refresh(settlement)

    return {
        "message": "提现申请已提交，等待超级管理员审批",
        "id": settlement.id,
        "amount": float(settlement.amount),
        "status": settlement.status,
    }


@router.get("/withdrawals")
def list_withdrawals(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    user: User = Depends(require_any_admin),
    db: Session = Depends(get_db),
):
    """查看自己的提现记录"""
    rider = db.query(Rider).filter(Rider.user_id == user.id).first()
    if not rider:
        return {"total": 0, "items": []}

    query = db.query(Settlement).filter(
        Settlement.target_type == "rider",
        Settlement.target_id == rider.id,
    )
    total = query.count()
    items = query.order_by(Settlement.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return {
        "total": total,
        "items": [{
            "id": s.id,
            "amount": float(s.amount),
            "status": s.status,
            "period": s.period,
            "created_at": str(s.created_at),
            "paid_at": str(s.paid_at) if s.paid_at else None,
        } for s in items],
    }
