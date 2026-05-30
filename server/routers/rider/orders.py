import json
from datetime import datetime, date
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func

from auth import require_rider
from database import get_db
from models.user import User
from models.rider import Rider
from models.order import CombinedOrder, SubOrder, SubOrderTimeline, OrderMessage
from models.region import Settlement, SystemConfig
from schemas.order import (
    CombinedOrderOut, CombinedOrderDetailOut, CombinedOrderListOut,
    SubOrderOut, SubOrderDetailOut, SubOrderItemOut, SubOrderTimelineOut,
    OrderMessageOut, OrderMessageCreate,
)
from websocket import manager


class RiderRegisterIn(BaseModel):
    real_name: str = Field(..., min_length=1, max_length=50)
    phone: str = Field(..., min_length=11, max_length=20)
    id_card: str = ""
    district_id: int = Field(...)

router = APIRouter(prefix="/api/rider/orders", tags=["骑手端-订单"])


def _get_rider(user: User, db: Session) -> Rider:
    rider = db.query(Rider).filter(Rider.user_id == user.id).first()
    if not rider:
        raise HTTPException(status_code=404, detail="请先完成骑手注册")
    return rider


def _add_sub_timeline(sub_order_id: int, status: str, description: str, db: Session):
    db.add(SubOrderTimeline(sub_order_id=sub_order_id, status=status, description=description))


def _combined_order_summary(order, rider_name: str = "") -> dict:
    store_count = len(order.sub_orders or [])
    return {
        "id": order.id, "order_no": order.order_no, "status": order.status,
        "user_id": order.user_id, "rider_id": order.rider_id,
        "total_price": float(order.total_price),
        "store_count": store_count,
        "rider_name": rider_name,
    }


@router.post("/register")
def register_rider(
    body: RiderRegisterIn,
    user: User = Depends(require_rider),
    db: Session = Depends(get_db),
):
    existing = db.query(Rider).filter(Rider.user_id == user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="已注册过骑手")

    rider = Rider(
        user_id=user.id,
        real_name=body.real_name,
        phone=body.phone,
        id_card=body.id_card,
        district_id=body.district_id,
    )
    db.add(rider)
    db.commit()
    db.refresh(rider)
    return {"message": "骑手注册成功，请等待审核", "rider_id": rider.id}


@router.get("/pending")
def pending_orders(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    user: User = Depends(require_rider),
    db: Session = Depends(get_db),
):
    rider = _get_rider(user, db)
    # 找出该分区所有 pending 状态的总单
    candidates = db.query(CombinedOrder).filter(
        CombinedOrder.status == "pending",
        CombinedOrder.district_id == rider.district_id,
    ).all()

    # 筛选：所有非取消子单都已 ready
    ready_orders = []
    for order in candidates:
        non_cancelled = [s for s in order.sub_orders if s.status != "cancelled"]
        if non_cancelled and all(s.status == "ready" for s in non_cancelled):
            ready_orders.append(order)

    # 分页
    total = len(ready_orders)
    ready_orders.sort(key=lambda o: o.created_at or datetime.min)
    paged = ready_orders[(page - 1) * page_size: page * page_size]

    result_items = []
    for order in paged:
        o = CombinedOrderOut.model_validate(order)
        o.sub_orders = [SubOrderOut.model_validate(s) for s in (order.sub_orders or [])]
        for so in o.sub_orders:
            so.store_name = so.store_name_snapshot
        result_items.append(o)

    return {"total": total, "items": [o.model_dump() for o in result_items]}


@router.post("/{order_id}/accept")
def accept_order(order_id: int, user: User = Depends(require_rider), db: Session = Depends(get_db)):
    rider = _get_rider(user, db)
    if rider.status == "offline":
        raise HTTPException(status_code=400, detail="请先上线")
    if rider.audit_status != "approved":
        raise HTTPException(status_code=400, detail="账号尚未通过审核")

    order = db.query(CombinedOrder).filter(CombinedOrder.id == order_id).with_for_update().first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status != "pending":
        raise HTTPException(status_code=400, detail="该订单已被其他骑手接单")
    if order.district_id != rider.district_id:
        raise HTTPException(status_code=400, detail="该订单不在你的配送区域")

    order.rider_id = rider.id
    order.status = "delivering"
    order.picked_at = datetime.now()
    rider.status = "busy"

    for sub in order.sub_orders:
        if sub.status == "cancelled":
            continue
        sub.status = "delivering"
        _add_sub_timeline(sub.id, "delivering", f"骑手 {rider.real_name} 已取餐，正在配送", db)

    db.commit()
    db.refresh(order)

    merchant_ids = {sub.store.user_id for sub in order.sub_orders if sub.store and sub.status != "cancelled"}
    summary = _combined_order_summary(order, rider.real_name)
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
    result.rider_name = rider.real_name
    result.sub_orders = [SubOrderOut.model_validate(s) for s in (order.sub_orders or [])]
    for so in result.sub_orders:
        so.store_name = so.store_name_snapshot
    return result


@router.put("/{order_id}/deliver")
def mark_delivered(order_id: int, user: User = Depends(require_rider), db: Session = Depends(get_db)):
    rider = _get_rider(user, db)
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
    rider.total_orders += 1
    rider.balance = float(rider.balance) + rider_earning

    timeline_msgs = []

    for sub in order.sub_orders:
        if sub.status == "cancelled":
            continue
        sub.status = "completed"

        items_total = float(sub.items_total)

        # 阶梯佣金计算
        rate = float(sub.commission_rate)  # 兜底默认
        district_rate = 0.0
        try:
            # 查询店铺当月累计销售额
            monthly_sales = db.query(func.coalesce(func.sum(SubOrder.items_total), 0)).filter(
                SubOrder.store_id == sub.store_id,
                SubOrder.status == "completed",
                func.strftime('%Y-%m', SubOrder.updated_at) == func.strftime('%Y-%m', 'now'),
            ).scalar() or 0
            # 匹配平台阶梯
            ct_cfg = db.query(SystemConfig).filter(SystemConfig.config_key == "commission_tiers").first()
            if ct_cfg:
                tiers = json.loads(ct_cfg.config_value) if ct_cfg.config_value else []
                tier_rate = None
                for t in tiers:
                    t_min = float(t.get("min", 0))
                    t_max = float(t.get("max", -1))
                    if monthly_sales >= t_min and (t_max < 0 or monthly_sales < t_max):
                        tier_rate = float(t.get("rate", 0))
                        break
                if tier_rate is not None:
                    rate = tier_rate
            # 匹配分区阶梯
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
        _add_sub_timeline(sub.id, "completed",
                          f"骑手已送达 | 商品¥{items_total:.2f} 平台扣¥{platform_fee:.2f}"
                          + (f" 分区扣¥{district_fee:.2f}" if district_fee > 0 else "")
                          + f" 商家得¥{merchant_net:.2f}", db)
        timeline_msgs.append(f"{sub.store_name_snapshot}: ¥{items_total:.2f}")

    # 检查是否有部分取消
    if any(s.status == "cancelled" for s in order.sub_orders):
        order.status = "partial"

    db.commit()
    db.refresh(order)

    merchant_ids = {sub.store.user_id for sub in order.sub_orders if sub.store and sub.status != "cancelled"}
    summary = _combined_order_summary(order, rider.real_name)
    summary["settlement"] = timeline_msgs
    manager.push_order_event_sync("order_delivered", summary, user_id=order.user_id)
    for mid in merchant_ids:
        manager.push_order_event_sync("order_delivered", summary, merchant_user_id=mid)

    result = CombinedOrderOut.model_validate(order)
    result.rider_name = rider.real_name
    result.sub_orders = [SubOrderOut.model_validate(s) for s in (order.sub_orders or [])]
    for so in result.sub_orders:
        so.store_name = so.store_name_snapshot
    return result


@router.put("/{order_id}/delivery-photo")
def upload_delivery_photo(
    order_id: int,
    photo_url: str = Body(..., embed=True),
    user: User = Depends(require_rider),
    db: Session = Depends(get_db),
):
    """骑手拍照上传送达凭证"""
    rider = db.query(Rider).filter(Rider.user_id == user.id).first()
    if not rider:
        raise HTTPException(status_code=403, detail="仅骑手可操作")
    order = db.query(CombinedOrder).filter(
        CombinedOrder.id == order_id, CombinedOrder.rider_id == rider.id
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status not in ("delivering", "completed", "partial"):
        raise HTTPException(status_code=400, detail="当前状态不可上传照片")

    order.delivery_photo = photo_url
    db.commit()

    # 推送给用户和管理端
    manager.push_order_event_sync(
        "delivery_photo_uploaded",
        {"order_id": order.id, "delivery_photo": photo_url},
        user_id=order.user_id,
    )
    manager.push_order_event_sync(
        "delivery_photo_uploaded",
        {"order_id": order.id, "delivery_photo": photo_url},
        broadcast_role="admin",
    )

    return {"message": "送达照片已上传", "delivery_photo": photo_url}


@router.get("/my")
def my_orders(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    user: User = Depends(require_rider),
    db: Session = Depends(get_db),
):
    rider = _get_rider(user, db)
    query = db.query(CombinedOrder).filter(CombinedOrder.rider_id == rider.id)
    total = query.count()
    items = query.order_by(CombinedOrder.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    result_items = []
    for order in items:
        o = CombinedOrderOut.model_validate(order)
        o.rider_name = rider.real_name
        o.sub_orders = [SubOrderOut.model_validate(s) for s in (order.sub_orders or [])]
        for so in o.sub_orders:
            so.store_name = so.store_name_snapshot
        result_items.append(o)

    return {"total": total, "items": [o.model_dump() for o in result_items]}


@router.get("/wallet")
def wallet(user: User = Depends(require_rider), db: Session = Depends(get_db)):
    rider = _get_rider(user, db)
    today = date.today()

    # 今日骑手收入 = 今日完成单数 × 每单收入
    today_count = db.query(func.count(CombinedOrder.id)).filter(
        CombinedOrder.rider_id == rider.id,
        CombinedOrder.status.in_(["completed", "partial"]),
        func.date(CombinedOrder.completed_at) == today,
    ).scalar() or 0

    rider_cfg = db.query(SystemConfig).filter(SystemConfig.config_key == "rider_per_order").first()
    rider_earning = float(rider_cfg.config_value) if rider_cfg else 5.0
    today_income = today_count * rider_earning

    recent = db.query(CombinedOrder).filter(
        CombinedOrder.rider_id == rider.id,
        CombinedOrder.status.in_(["completed", "partial"]),
    ).order_by(CombinedOrder.completed_at.desc()).limit(5).all()

    return {
        "status": rider.status or "offline",
        "balance": float(rider.balance),
        "total_orders": rider.total_orders,
        "rating": float(rider.rating),
        "today_income": float(today_income),
        "recent_orders": [
            {
                "id": o.id, "order_no": o.order_no,
                "store_count": len([s for s in (o.sub_orders or []) if s.status != "cancelled"]),
                "total_price": float(o.total_price),
                "completed_at": str(o.completed_at),
            }
            for o in recent
        ],
    }


@router.post("/withdraw")
def withdraw(
    amount: float = Body(..., gt=0, embed=True),
    user: User = Depends(require_rider),
    db: Session = Depends(get_db),
):
    rider = _get_rider(user, db)
    if amount > float(rider.balance):
        raise HTTPException(status_code=400, detail="余额不足")
    if amount < 1:
        raise HTTPException(status_code=400, detail="结算金额不能少于1元")

    # 创建结算申请记录，等待管理员线下打款后确认
    from models.region import Settlement
    settlement = Settlement(
        target_type="rider",
        target_id=rider.id,
        amount=amount,
        fee=0,
        net_amount=amount,
        status="pending",
    )
    db.add(settlement)
    db.commit()

    return {
        "message": f"已提交 ¥{amount:.2f} 结算申请，等待管理员处理",
        "settlement_id": settlement.id,
        "amount": amount,
    }


@router.get("/settlements")
def list_settlements(
    user: User = Depends(require_rider),
    db: Session = Depends(get_db),
):
    """骑手查看自己的结算申请记录"""
    rider = _get_rider(user, db)
    from models.region import Settlement
    records = db.query(Settlement).filter(
        Settlement.target_type == "rider",
        Settlement.target_id == rider.id,
    ).order_by(Settlement.created_at.desc()).limit(20).all()

    return {
        "items": [
            {
                "id": r.id,
                "amount": float(r.amount),
                "net_amount": float(r.net_amount),
                "status": r.status,
                "created_at": str(r.created_at),
                "paid_at": str(r.paid_at) if r.paid_at else None,
            }
            for r in records
        ]
    }


@router.get("/{order_id}")
def get_order(order_id: int, user: User = Depends(require_rider), db: Session = Depends(get_db)):
    rider = _get_rider(user, db)
    order = db.query(CombinedOrder).filter(CombinedOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.rider_id and order.rider_id != rider.id:
        # 未分配骑手且在骑手分区内则允许查看
        if not order.rider_id and order.district_id != rider.district_id:
            raise HTTPException(status_code=403, detail="该订单不在你的配送区域")
        elif order.rider_id:
            raise HTTPException(status_code=403, detail="该订单已被其他骑手接单")

    result = CombinedOrderDetailOut.model_validate(order)
    result.rider_name = order.rider.real_name if order.rider else ""
    result.sub_orders = []
    for sub in (order.sub_orders or []):
        sd = SubOrderDetailOut.model_validate(sub)
        sd.store_name = sub.store.name if sub.store else sub.store_name_snapshot
        sd.items = [SubOrderItemOut.model_validate(i) for i in (sub.items or [])]
        sd.timeline = [
            SubOrderTimelineOut.model_validate(t)
            for t in (sub.timeline.order_by(SubOrderTimeline.created_at.asc()).all() if sub.timeline else [])
        ]
        result.sub_orders.append(sd)
    return result


@router.put("/status")
def update_status(
    status: str = Query(...),
    user: User = Depends(require_rider),
    db: Session = Depends(get_db),
):
    rider = _get_rider(user, db)
    if status not in ("online", "offline", "busy"):
        raise HTTPException(status_code=400, detail="无效状态")
    rider.status = status
    db.commit()
    return {"message": f"状态已切换为 {status}", "status": status}


@router.put("/location")
def update_location(
    lat: float = Query(...),
    lng: float = Query(...),
    user: User = Depends(require_rider),
    db: Session = Depends(get_db),
):
    rider = _get_rider(user, db)
    rider.lat = lat
    rider.lng = lng
    db.commit()

    active_orders = db.query(CombinedOrder).filter(
        CombinedOrder.rider_id == rider.id,
        CombinedOrder.status == "delivering",
    ).all()
    for order in active_orders:
        manager.push_order_event_sync(
            "rider_location",
            {"order_id": order.id, "rider_id": rider.id, "rider_name": rider.real_name,
             "lat": lat, "lng": lng},
            user_id=order.user_id,
        )

    return {"message": "位置已更新"}


# ---- 订单留言 ----
@router.get("/{order_id}/messages", response_model=List[OrderMessageOut])
def get_order_messages(
    order_id: int,
    user: User = Depends(require_rider),
    db: Session = Depends(get_db),
):
    """查看订单留言"""
    rider = _get_rider(user, db)
    order = db.query(CombinedOrder).filter(
        CombinedOrder.id == order_id,
        CombinedOrder.rider_id == rider.id,
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    msgs = db.query(OrderMessage).filter(
        OrderMessage.combined_order_id == order_id
    ).order_by(OrderMessage.created_at).all()
    return [OrderMessageOut.model_validate(m) for m in msgs]


@router.post("/{order_id}/messages", response_model=OrderMessageOut)
def send_order_message(
    order_id: int,
    body: OrderMessageCreate,
    user: User = Depends(require_rider),
    db: Session = Depends(get_db),
):
    """骑手发送留言"""
    rider = _get_rider(user, db)
    order = db.query(CombinedOrder).filter(
        CombinedOrder.id == order_id,
        CombinedOrder.rider_id == rider.id,
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status in ("completed", "cancelled"):
        raise HTTPException(status_code=400, detail="订单已结束，不能留言")

    msg = OrderMessage(
        combined_order_id=order_id,
        sender_id=user.id,
        sender_role="rider",
        content=body.content,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    # WebSocket 推送给用户
    manager.push_order_event_sync(
        "new_message", {
            "order_id": order_id, "order_no": order.order_no,
            "sender_role": "rider", "content": body.content,
            "rider_name": rider.real_name,
        },
        user_id=order.user_id,
    )

    return OrderMessageOut.model_validate(msg)
