from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from auth import require_rider
from database import get_db
from models.user import User
from models.rider import Rider
from models.order import Order, OrderTimeline
from schemas.order import OrderOut, OrderDetailOut, OrderListOut
from websocket import manager

router = APIRouter(prefix="/api/rider/orders", tags=["骑手端-订单"])


def _get_rider(user: User, db: Session) -> Rider:
    rider = db.query(Rider).filter(Rider.user_id == user.id).first()
    if not rider:
        raise HTTPException(status_code=404, detail="请先完成骑手注册")
    return rider


def _add_timeline(order_id: int, status: str, description: str, db: Session):
    db.add(OrderTimeline(order_id=order_id, status=status, description=description))


def _order_summary(order, restaurant_name: str = "", rider_name: str = "") -> dict:
    return {
        "id": order.id, "order_no": order.order_no, "status": order.status,
        "user_id": order.user_id, "restaurant_id": order.restaurant_id,
        "rider_id": order.rider_id, "total_price": float(order.total_price),
        "restaurant_name": restaurant_name, "rider_name": rider_name,
    }


@router.get("/pending", response_model=OrderListOut)
def pending_orders(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    user: User = Depends(require_rider),
    db: Session = Depends(get_db),
):
    """可接的待配送订单"""
    rider = _get_rider(user, db)
    query = db.query(Order).filter(
        Order.status == "ready",
        Order.region_id == rider.region_id,
    )

    total = query.count()
    items = query.order_by(Order.ready_at.asc()).offset((page - 1) * page_size).limit(page_size).all()

    result_items = []
    for order in items:
        o = OrderOut.model_validate(order)
        o.restaurant_name = order.restaurant.name if order.restaurant else ""
        result_items.append(o)

    return OrderListOut(total=total, items=result_items)


@router.post("/{order_id}/accept", response_model=OrderOut)
def accept_order(order_id: int, user: User = Depends(require_rider), db: Session = Depends(get_db)):
    rider = _get_rider(user, db)
    if rider.status == "offline":
        raise HTTPException(status_code=400, detail="请先上线")

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status != "ready":
        raise HTTPException(status_code=400, detail="该订单已被其他骑手接单")
    if order.region_id != rider.region_id:
        raise HTTPException(status_code=400, detail="该订单不在你的配送区域")

    order.rider_id = rider.id
    order.status = "delivering"
    order.picked_at = datetime.now()
    rider.status = "busy"
    _add_timeline(order.id, "delivering", f"骑手 {rider.real_name} 已取餐，正在配送", db)
    db.commit()
    db.refresh(order)
    # 通知用户和商家
    restaurant_name = order.restaurant.name if order.restaurant else ""
    merchant_uid = order.restaurant.user_id if order.restaurant else None
    summary = _order_summary(order, restaurant_name, rider.real_name)
    manager.push_order_event_sync("rider_accepted", summary, user_id=order.user_id, merchant_user_id=merchant_uid)
    # 推送骑手初始位置
    if rider.lat is not None and rider.lng is not None:
        manager.push_order_event_sync(
            "rider_location",
            {"order_id": order.id, "rider_id": rider.id, "rider_name": rider.real_name,
             "lat": float(rider.lat), "lng": float(rider.lng)},
            user_id=order.user_id,
        )
    result = OrderOut.model_validate(order)
    result.restaurant_name = restaurant_name
    result.rider_name = rider.real_name
    return result


@router.put("/{order_id}/deliver", response_model=OrderOut)
def mark_delivered(order_id: int, user: User = Depends(require_rider), db: Session = Depends(get_db)):
    rider = _get_rider(user, db)
    order = db.query(Order).filter(Order.id == order_id, Order.rider_id == rider.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status != "delivering":
        raise HTTPException(status_code=400, detail="当前状态不可确认送达")

    order.status = "completed"
    order.delivered_at = datetime.now()
    order.completed_at = datetime.now()
    rider.status = "online"
    rider.total_orders += 1
    rider.balance = float(rider.balance) + 5
    _add_timeline(order.id, "completed", "骑手已送达，订单完成", db)
    db.commit()
    db.refresh(order)
    # 通知用户和商家
    restaurant_name = order.restaurant.name if order.restaurant else ""
    merchant_uid = order.restaurant.user_id if order.restaurant else None
    summary = _order_summary(order, restaurant_name, rider.real_name)
    manager.push_order_event_sync("order_delivered", summary, user_id=order.user_id, merchant_user_id=merchant_uid)
    result = OrderOut.model_validate(order)
    result.restaurant_name = restaurant_name
    result.rider_name = rider.real_name
    return result


@router.get("/my", response_model=OrderListOut)
def my_orders(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    user: User = Depends(require_rider),
    db: Session = Depends(get_db),
):
    """骑手的配送记录"""
    rider = _get_rider(user, db)
    query = db.query(Order).filter(Order.rider_id == rider.id)
    total = query.count()
    items = query.order_by(Order.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    result_items = []
    for order in items:
        o = OrderOut.model_validate(order)
        o.restaurant_name = order.restaurant.name if order.restaurant else ""
        o.rider_name = rider.real_name
        result_items.append(o)

    return OrderListOut(total=total, items=result_items)


@router.put("/status")
def update_status(
    status: str = Query(...),
    user: User = Depends(require_rider),
    db: Session = Depends(get_db),
):
    """骑手上下线"""
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
    """上报骑手位置，同步推送给相关订单的用户"""
    rider = _get_rider(user, db)
    rider.lat = lat
    rider.lng = lng
    db.commit()

    # 推送给该骑手所有配送中订单的用户
    active_orders = db.query(Order).filter(
        Order.rider_id == rider.id,
        Order.status == "delivering",
    ).all()
    for order in active_orders:
        manager.push_order_event_sync(
            "rider_location",
            {
                "order_id": order.id,
                "rider_id": rider.id,
                "rider_name": rider.real_name,
                "lat": lat,
                "lng": lng,
            },
            user_id=order.user_id,
        )

    return {"message": "位置已更新"}


@router.get("/wallet")
def wallet(user: User = Depends(require_rider), db: Session = Depends(get_db)):
    rider = _get_rider(user, db)
    return {
        "balance": float(rider.balance),
        "total_orders": rider.total_orders,
        "rating": float(rider.rating),
    }
