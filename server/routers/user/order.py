import math
import random
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from auth import require_user
from database import get_db
from models.user import User, UserAddress
from models.restaurant import Restaurant, MenuItem
from models.rider import Rider
from models.order import Order, OrderItem, OrderTimeline
from schemas.order import OrderCreate, OrderOut, OrderDetailOut, OrderListOut
from schemas.payment import PayParamsOut, RefundIn
from payment import create_jsapi_order, apply_refund
from websocket import manager

router = APIRouter(prefix="/api/user/orders", tags=["用户端-订单"])


def _generate_order_no() -> str:
    now = datetime.now()
    return now.strftime("%Y%m%d%H%M%S") + str(random.randint(1000, 9999))


def _add_timeline(order_id: int, status: str, description: str, db: Session):
    db.add(OrderTimeline(order_id=order_id, status=status, description=description))


def _order_summary(order, restaurant_name: str = "", rider_name: str = "") -> dict:
    return {
        "id": order.id, "order_no": order.order_no, "status": order.status,
        "user_id": order.user_id, "restaurant_id": order.restaurant_id,
        "rider_id": order.rider_id, "total_price": float(order.total_price),
        "restaurant_name": restaurant_name, "rider_name": rider_name,
    }


@router.post("", response_model=OrderOut)
def create_order(
    body: OrderCreate,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    # 验证餐厅
    restaurant = db.query(Restaurant).filter(
        Restaurant.id == body.restaurant_id,
        Restaurant.status == "open",
        Restaurant.verify_status == "verified",
    ).first()
    if not restaurant:
        raise HTTPException(status_code=400, detail="餐厅不可用")

    # 验证地址
    address = db.query(UserAddress).filter(
        UserAddress.id == body.address_id,
        UserAddress.user_id == user.id,
    ).first()
    if not address:
        raise HTTPException(status_code=400, detail="地址不存在")

    # 计算价格
    items_total = 0
    order_items = []
    for item_in in body.items:
        menu_item = db.query(MenuItem).filter(
            MenuItem.id == item_in.menu_item_id,
            MenuItem.status == 1,
        ).first()
        if not menu_item:
            raise HTTPException(status_code=400, detail=f"菜品 {item_in.name} 已下架")
        price = float(menu_item.price)
        items_total += price * item_in.quantity
        order_items.append(OrderItem(
            menu_item_id=menu_item.id,
            name=menu_item.name,
            image=menu_item.image,
            price=price,
            quantity=item_in.quantity,
        ))

    delivery_fee = float(restaurant.delivery_fee)
    package_fee = 1.0  # 包装费
    total_price = items_total + delivery_fee + package_fee

    if items_total < float(restaurant.min_price):
        raise HTTPException(status_code=400, detail=f"未达到起送价 ¥{float(restaurant.min_price)}")

    # 创建订单 — 状态: pending_pay 待支付
    order = Order(
        order_no=_generate_order_no(),
        user_id=user.id,
        restaurant_id=restaurant.id,
        address_snapshot={
            "contact_name": address.contact_name,
            "contact_phone": address.contact_phone,
            "gender": address.gender,
            "province": address.province,
            "city": address.city,
            "district": address.district,
            "detail": address.detail,
            "lat": float(address.lat) if address.lat else None,
            "lng": float(address.lng) if address.lng else None,
        },
        items_total=items_total,
        delivery_fee=delivery_fee,
        package_fee=package_fee,
        total_price=total_price,
        status="pending_pay",
        remark=body.remark,
        region_id=restaurant.region_id,
    )
    order.items = order_items
    db.add(order)
    db.flush()

    _add_timeline(order.id, "pending_pay", "订单已创建，等待支付", db)
    db.commit()
    db.refresh(order)

    result = OrderOut.model_validate(order)
    result.restaurant_name = restaurant.name
    return result


@router.post("/{order_id}/pay", response_model=PayParamsOut)
def pay_order(
    order_id: int,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """
    发起微信支付 — 返回 wx.requestPayment 所需参数
    未配置微信支付时返回模拟数据
    """
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == user.id,
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status != "pending_pay":
        raise HTTPException(status_code=400, detail="订单状态不正确")

    total_fen = math.floor(float(order.total_price) * 100)  # 元 → 分
    description = f"外卖订单 {order.order_no}"
    result = create_jsapi_order(order.order_no, total_fen, description, user.openid)

    # 模拟模式下直接标记支付成功 (无回调)
    if result.get("isMock"):
        order.status = "pending_accept"
        order.paid_at = datetime.now()
        _add_timeline(order.id, "pending_accept", "支付成功(模拟)，等待商家接单", db)
        db.commit()
        db.refresh(order)
        # 推送新订单通知给商家
        merchant_uid = order.restaurant.user_id if order.restaurant else None
        manager.push_order_event_sync(
            "order_paid", _order_summary(order, order.restaurant.name if order.restaurant else ""),
            merchant_user_id=merchant_uid)

    return result


@router.post("/{order_id}/refund", response_model=OrderOut)
def refund_order(
    order_id: int,
    reason: str = Query(default=""),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """
    申请退款 — 调用微信支付退款接口
    未配置微信支付时直接标记退款
    """
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == user.id,
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status not in ("pending_accept",):
        raise HTTPException(status_code=400, detail="当前状态不可退款")

    refund_amount = math.floor(float(order.total_price) * 100)
    total_amount = math.floor(float(order.total_price) * 100)
    apply_refund(order.order_no, refund_amount, total_amount, reason)

    order.status = "cancelled"
    order.cancel_reason = reason or "用户申请退款"
    order.cancel_by = "user"
    _add_timeline(order.id, "cancelled", f"用户申请退款: {reason or '无理由'}", db)
    db.commit()
    db.refresh(order)
    # 推送退款通知
    merchant_uid = order.restaurant.user_id if order.restaurant else None
    manager.push_order_event_sync(
        "order_refunded", _order_summary(order, order.restaurant.name if order.restaurant else ""),
        merchant_user_id=merchant_uid)

    result = OrderOut.model_validate(order)
    result.restaurant_name = order.restaurant.name if order.restaurant else ""
    return result


@router.get("", response_model=OrderListOut)
def list_orders(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    status: str = Query(default=""),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    query = db.query(Order).filter(Order.user_id == user.id)
    if status:
        query = query.filter(Order.status == status)

    total = query.count()
    items = query.order_by(Order.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    result_items = []
    for order in items:
        o = OrderOut.model_validate(order)
        o.restaurant_name = order.restaurant.name if order.restaurant else ""
        o.rider_name = order.rider.real_name if order.rider else ""
        result_items.append(o)

    return OrderListOut(total=total, items=result_items)


@router.get("/{order_id}", response_model=OrderDetailOut)
def get_order(
    order_id: int,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == user.id,
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    result = OrderDetailOut.model_validate(order)
    result.restaurant_name = order.restaurant.name if order.restaurant else ""
    result.rider_name = order.rider.real_name if order.rider else ""
    result.timeline = order.timeline.all()
    return result


@router.get("/{order_id}/rider-location")
def get_rider_location(
    order_id: int,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """查询订单骑手实时位置 (配送中时可用)"""
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == user.id,
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status != "delivering":
        raise HTTPException(status_code=400, detail="骑手尚未取餐")

    rider = db.query(Rider).filter(Rider.id == order.rider_id).first()
    if not rider or rider.lat is None or rider.lng is None:
        raise HTTPException(status_code=404, detail="暂无骑手位置信息")

    return {
        "order_id": order.id,
        "rider_id": rider.id,
        "rider_name": rider.real_name,
        "lat": float(rider.lat),
        "lng": float(rider.lng),
        "phone": rider.phone,
    }


@router.put("/{order_id}/cancel", response_model=OrderOut)
def cancel_order(
    order_id: int,
    reason: str = Query(default=""),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == user.id,
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status not in ("pending_pay", "pending_accept"):
        raise HTTPException(status_code=400, detail="当前状态不可取消")

    order.status = "cancelled"
    order.cancel_reason = reason or "用户取消"
    order.cancel_by = "user"
    _add_timeline(order.id, "cancelled", f"用户取消订单: {reason or '无理由'}", db)
    db.commit()
    db.refresh(order)
    # 推送取消通知
    merchant_uid = order.restaurant.user_id if order.restaurant else None
    manager.push_order_event_sync(
        "order_cancelled", _order_summary(order, order.restaurant.name if order.restaurant else ""),
        merchant_user_id=merchant_uid)

    result = OrderOut.model_validate(order)
    result.restaurant_name = order.restaurant.name if order.restaurant else ""
    return result
