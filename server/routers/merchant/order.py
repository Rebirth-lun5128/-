from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from auth import require_merchant
from database import get_db
from models.user import User
from models.restaurant import Restaurant
from models.order import Order, OrderTimeline
from schemas.order import OrderOut, OrderDetailOut, OrderListOut
from websocket import manager

router = APIRouter(prefix="/api/merchant/orders", tags=["商家端-订单"])


def _get_restaurant(user: User, db: Session) -> Restaurant:
    r = db.query(Restaurant).filter(Restaurant.user_id == user.id).first()
    if not r:
        raise HTTPException(status_code=404, detail="请先入驻")
    return r


def _add_timeline(order_id: int, status: str, description: str, db: Session):
    db.add(OrderTimeline(order_id=order_id, status=status, description=description))


def _order_summary(order, restaurant_name: str = "") -> dict:
    return {
        "id": order.id, "order_no": order.order_no, "status": order.status,
        "user_id": order.user_id, "restaurant_id": order.restaurant_id,
        "rider_id": order.rider_id, "total_price": float(order.total_price),
        "restaurant_name": restaurant_name,
    }


@router.get("", response_model=OrderListOut)
def list_orders(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    status: str = Query(default=""),
    user: User = Depends(require_merchant),
    db: Session = Depends(get_db),
):
    restaurant = _get_restaurant(user, db)
    query = db.query(Order).filter(Order.restaurant_id == restaurant.id)
    if status:
        query = query.filter(Order.status == status)

    total = query.count()
    items = query.order_by(Order.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    result_items = []
    for order in items:
        o = OrderOut.model_validate(order)
        o.restaurant_name = restaurant.name
        result_items.append(o)

    return OrderListOut(total=total, items=result_items)


@router.get("/{order_id}", response_model=OrderDetailOut)
def get_order(order_id: int, user: User = Depends(require_merchant), db: Session = Depends(get_db)):
    restaurant = _get_restaurant(user, db)
    order = db.query(Order).filter(Order.id == order_id, Order.restaurant_id == restaurant.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    result = OrderDetailOut.model_validate(order)
    result.restaurant_name = restaurant.name
    result.timeline = order.timeline.all()
    return result


@router.put("/{order_id}/accept", response_model=OrderOut)
def accept_order(order_id: int, user: User = Depends(require_merchant), db: Session = Depends(get_db)):
    restaurant = _get_restaurant(user, db)
    order = db.query(Order).filter(Order.id == order_id, Order.restaurant_id == restaurant.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status != "pending_accept":
        raise HTTPException(status_code=400, detail="当前状态不可接单")

    order.status = "preparing"
    order.accepted_at = datetime.now()
    _add_timeline(order.id, "preparing", "商家已接单，正在准备餐品", db)
    db.commit()
    db.refresh(order)
    manager.push_order_event_sync(
        "order_accepted", _order_summary(order, restaurant.name), user_id=order.user_id)
    result = OrderOut.model_validate(order)
    result.restaurant_name = restaurant.name
    return result


@router.put("/{order_id}/reject", response_model=OrderOut)
def reject_order(order_id: int, reason: str = Query(default=""), user: User = Depends(require_merchant), db: Session = Depends(get_db)):
    restaurant = _get_restaurant(user, db)
    order = db.query(Order).filter(Order.id == order_id, Order.restaurant_id == restaurant.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status != "pending_accept":
        raise HTTPException(status_code=400, detail="当前状态不可拒单")

    order.status = "cancelled"
    order.cancel_reason = reason or "商家拒单"
    order.cancel_by = "merchant"
    _add_timeline(order.id, "cancelled", f"商家拒单: {reason or '暂无法接单'}", db)
    db.commit()
    db.refresh(order)
    manager.push_order_event_sync(
        "order_rejected", _order_summary(order, restaurant.name), user_id=order.user_id)
    result = OrderOut.model_validate(order)
    result.restaurant_name = restaurant.name
    return result


@router.put("/{order_id}/ready", response_model=OrderOut)
def mark_ready(order_id: int, user: User = Depends(require_merchant), db: Session = Depends(get_db)):
    restaurant = _get_restaurant(user, db)
    order = db.query(Order).filter(Order.id == order_id, Order.restaurant_id == restaurant.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status != "preparing":
        raise HTTPException(status_code=400, detail="当前状态不可出餐")

    order.status = "ready"
    order.ready_at = datetime.now()
    _add_timeline(order.id, "ready", "餐品已准备完成，等待骑手取餐", db)
    db.commit()
    db.refresh(order)
    # 通知用户和可接单的骑手
    manager.push_order_event_sync(
        "order_ready", _order_summary(order, restaurant.name), user_id=order.user_id)
    manager.push_order_event_sync(
        "new_delivery", _order_summary(order, restaurant.name))
    result = OrderOut.model_validate(order)
    result.restaurant_name = restaurant.name
    return result
