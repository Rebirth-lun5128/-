import math
import random
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from auth import require_user
from database import get_db
from ratelimit import general_limiter
from models.user import User, UserAddress
from models.store import Store, Product
from models.rider import Rider
from models.district import District
from models.order import CombinedOrder, SubOrder, SubOrderItem, SubOrderTimeline, OrderReview, OrderModification, OrderMessage
from models.coupon import Coupon, UserCoupon
from schemas.order import (
    CombinedOrderCreate, CombinedOrderOut, CombinedOrderDetailOut, CombinedOrderListOut,
    SubOrderOut, SubOrderDetailOut, SubOrderItemOut, SubOrderTimelineOut,
    ReviewCreate, ReviewOut, ModificationCreate, ModificationOut,
    OrderMessageOut, OrderMessageCreate,
)
from schemas.payment import PayParamsOut
from payment import create_jsapi_order, apply_refund
from websocket import manager
from utils import mask_phone

router = APIRouter(prefix="/api/user/orders", tags=["用户端-订单"])


def _generate_order_no() -> str:
    now = datetime.now()
    return now.strftime("%Y%m%d%H%M%S") + str(random.randint(1000, 9999))


def _add_sub_timeline(sub_order_id: int, status: str, description: str, db: Session):
    db.add(SubOrderTimeline(sub_order_id=sub_order_id, status=status, description=description))


def _derive_combined_status(sub_orders: list) -> str:
    """根据子单状态推导总单聚合状态"""
    statuses = [s.status for s in sub_orders]
    if all(s == "cancelled" for s in statuses):
        return "cancelled"
    if any(s == "delivering" for s in statuses):
        return "delivering"
    if all(s in ("completed", "cancelled") for s in statuses):
        return "completed" if all(s == "completed" for s in statuses) else "partial"
    if all(s in ("pending_accept", "preparing", "ready") for s in statuses):
        return "pending"
    return "pending"


def _combined_order_out(order, rider_name: str = "") -> dict:
    """组装 CombinedOrderOut 数据（不含 sub_orders）"""
    return {
        "id": order.id, "order_no": order.order_no, "status": order.status,
        "user_id": order.user_id, "rider_id": order.rider_id,
        "items_total": float(order.items_total),
        "delivery_fee_original": float(order.delivery_fee_original),
        "delivery_fee_discount": float(order.delivery_fee_discount),
        "delivery_fee": float(order.delivery_fee),
        "package_fee": float(order.package_fee),
        "coupon_discount": float(order.coupon_discount),
        "total_price": float(order.total_price),
        "rider_name": rider_name,
    }


def _sub_order_out(sub) -> dict:
    return {
        "id": sub.id, "combined_order_id": sub.combined_order_id,
        "store_id": sub.store_id, "store_name_snapshot": sub.store_name_snapshot or "",
        "items_total": float(sub.items_total),
        "commission_rate": float(sub.commission_rate),
        "status": sub.status,
        "cancel_reason": sub.cancel_reason or "",
        "cancel_by": sub.cancel_by or "",
        "accepted_at": sub.accepted_at,
        "ready_at": sub.ready_at,
        "created_at": sub.created_at,
        "items": [SubOrderItemOut.model_validate(i).model_dump() for i in (sub.items or [])],
        "store_name": sub.store.name if sub.store else "",
    }


def _calculate_delivery_fee(district, store_surcharges: List[float], items_total: float) -> dict:
    """计算配送费，返回 {original, discount, final}"""
    now = datetime.now()
    is_peak = False
    base_fee_fen = district.delivery_fee or 0
    if district.peak_delivery_fee and district.peak_delivery_fee > 0:
        peak_start = district.peak_start_hour
        peak_end = district.peak_end_hour
        if peak_start is not None and peak_end is not None:
            is_peak = peak_start <= now.hour < peak_end
            if is_peak:
                base_fee_fen = district.peak_delivery_fee

    base_fee = base_fee_fen / 100.0
    max_surcharge = max(store_surcharges) if store_surcharges else 0
    original = round(base_fee + float(max_surcharge), 2)

    # 满减配送费规则匹配
    discount = 0
    rules = district.delivery_fee_rules or []
    for rule in rules:
        threshold = float(rule.get("threshold", 0))
        if items_total >= threshold:
            rule_type = rule.get("type", "")
            if rule_type == "free":
                discount = original
            elif rule_type == "reduce":
                discount = float(rule.get("reduce", 0))
            break  # 规则按优惠最大排序，命中第一条即停止

    discount = min(discount, original)
    final = round(max(0, original - discount), 2)
    return {"original": original, "discount": round(discount, 2), "final": final}


# ---- 创建总单 ----
@router.post("", response_model=CombinedOrderOut)
def create_order(
    body: CombinedOrderCreate,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
    _rl=Depends(general_limiter),
):
    address = db.query(UserAddress).filter(
        UserAddress.id == body.address_id,
        UserAddress.user_id == user.id,
    ).first()
    if not address:
        raise HTTPException(status_code=400, detail="地址不存在")

    # 获取分区（从第一个店铺所属分区）
    first_store = db.query(Store).filter(Store.id == body.sub_orders[0].store_id).first()
    if not first_store:
        raise HTTPException(status_code=400, detail="店铺不存在")
    district = db.query(District).filter(District.id == first_store.district_id).first()
    if not district:
        raise HTTPException(status_code=400, detail="分区不存在")

    # 校验所有子单
    sub_data = []
    items_total = 0
    store_surcharges = []
    for sub_in in body.sub_orders:
        store = db.query(Store).filter(
            Store.id == sub_in.store_id,
            Store.status == "open",
            Store.verify_status == "verified",
        ).first()
        if not store:
            raise HTTPException(status_code=400, detail=f"店铺(ID={sub_in.store_id})不可用")
        combinable = store.combinable_districts or []
        if store.district_id != district.id and district.id not in combinable:
            raise HTTPException(status_code=400, detail=f"店铺'{store.name}'不在同一分区，无法合单")

        sub_items_total = 0
        sub_items = []
        for item_in in sub_in.items:
            product = db.query(Product).filter(
                Product.id == item_in.product_id,
                Product.store_id == store.id,
                Product.status == 1,
            ).first()
            if not product:
                raise HTTPException(status_code=400, detail=f"商品'{item_in.name}'已下架")
            if product.limit_per_order > 0 and item_in.quantity > product.limit_per_order:
                raise HTTPException(status_code=400, detail=f"{product.name} 每单限购 {product.limit_per_order} 件")
            if product.stock >= 0 and item_in.quantity > product.stock:
                raise HTTPException(status_code=400, detail=f"{product.name} 库存不足")
            price = float(product.price)
            sub_items_total += price * item_in.quantity
            sub_items.append(SubOrderItem(
                product_id=product.id, name=product.name, image=product.image or "",
                price=price, quantity=item_in.quantity,
            ))
            if product.stock >= 0:
                product.stock -= item_in.quantity

        if sub_items_total < float(store.min_price):
            raise HTTPException(status_code=400, detail=f"店铺'{store.name}'未达到起送价 ¥{float(store.min_price)}")

        sub_data.append({
            "store": store, "items_total": sub_items_total, "items": sub_items,
        })
        items_total += sub_items_total
        store_surcharges.append(float(store.delivery_surcharge or 0))

    # 计算配送费
    fee = _calculate_delivery_fee(district, store_surcharges, items_total)

    # 优惠券
    coupon_discount = 0
    if body.user_coupon_id:
        uc = db.query(UserCoupon).filter(
            UserCoupon.id == body.user_coupon_id,
            UserCoupon.user_id == user.id,
            UserCoupon.status == "unused",
        ).first()
        if uc:
            coupon = db.query(Coupon).filter(Coupon.id == uc.coupon_id).first()
            if coupon:
                if coupon.coupon_type == "full_reduction" and items_total >= float(coupon.condition_amount or 0):
                    coupon_discount = float(coupon.discount_amount)
                elif coupon.coupon_type in ("direct_discount", "new_user"):
                    coupon_discount = float(coupon.discount_amount)
                uc.status = "used"
                uc.used_at = datetime.now()
                coupon.used_count = (coupon.used_count or 0) + 1

    total_price = round(max(0, items_total + fee["final"] - coupon_discount), 2)

    # 创建总单
    order = CombinedOrder(
        order_no=_generate_order_no(),
        user_id=user.id,
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
        delivery_fee_original=fee["original"],
        delivery_fee_discount=fee["discount"],
        delivery_fee=fee["final"],
        coupon_discount=coupon_discount,
        total_price=total_price,
        status="pending_pay",
        district_id=district.id,
        remark=body.remark,
        user_coupon_id=body.user_coupon_id,
    )
    db.add(order)
    db.flush()

    # 创建子单
    sub_orders = []
    for sd in sub_data:
        sub = SubOrder(
            combined_order_id=order.id,
            store_id=sd["store"].id,
            store_name_snapshot=sd["store"].name,
            items_total=sd["items_total"],
            commission_rate=float(sd["store"].commission_rate or 0.12),
            status="pending_accept",
        )
        sub.items = sd["items"]
        db.add(sub)
        db.flush()
        _add_sub_timeline(sub.id, "pending_accept", "子单已创建，等待商家接单", db)
        sub_orders.append(sub)

    db.commit()
    db.refresh(order)

    result = CombinedOrderOut.model_validate(order)
    result.sub_orders = [SubOrderOut.model_validate(s) for s in sub_orders]
    for so in result.sub_orders:
        so.store_name = next((sd["store"].name for sd in sub_data if sd["store"].id == so.store_id), "")
    return result


# ---- 支付 ----
@router.post("/{order_id}/pay", response_model=PayParamsOut)
def pay_order(
    order_id: int,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    order = db.query(CombinedOrder).filter(
        CombinedOrder.id == order_id,
        CombinedOrder.user_id == user.id,
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status != "pending_pay":
        raise HTTPException(status_code=400, detail="订单状态不正确")

    total_fen = math.floor(float(order.total_price) * 100)
    description = f"夜市外卖 {order.order_no}"
    result = create_jsapi_order(order.order_no, total_fen, description, user.openid)

    if result.get("isMock"):
        order.status = "pending"
        order.paid_at = datetime.now()
        for sub in order.sub_orders:
            sub.status = "pending_accept"
            _add_sub_timeline(sub.id, "pending_accept", "已支付，等待商家接单", db)
        db.commit()
        db.refresh(order)
        merchant_ids = {sub.store.user_id for sub in order.sub_orders if sub.store}
        summary = _combined_order_out(order)
        for mid in merchant_ids:
            manager.push_order_event_sync("order_paid", summary, merchant_user_id=mid)
        # 推送新订单通知给管理员/配送端
        manager.push_order_event_sync("new_order", summary, broadcast_role="admin")
        manager.push_order_event_sync("new_delivery", summary, broadcast_role="rider")

    return result


# ---- 订单列表 ----
@router.get("", response_model=CombinedOrderListOut)
def list_orders(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    status: str = Query(default=""),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    query = db.query(CombinedOrder).filter(CombinedOrder.user_id == user.id)
    if status:
        query = query.filter(CombinedOrder.status == status)

    total = query.count()
    items = query.order_by(CombinedOrder.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    result_items = []
    for order in items:
        o = CombinedOrderOut.model_validate(order)
        o.rider_name = order.rider.real_name if order.rider else ""
        o.sub_orders = [SubOrderOut.model_validate(s) for s in (order.sub_orders or [])]
        for so in o.sub_orders:
            so.store_name = so.store_name_snapshot
        result_items.append(o)

    return CombinedOrderListOut(total=total, items=result_items)


# ---- 订单详情 ----
@router.get("/{order_id}", response_model=CombinedOrderDetailOut)
def get_order(
    order_id: int,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    order = db.query(CombinedOrder).filter(
        CombinedOrder.id == order_id,
        CombinedOrder.user_id == user.id,
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

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


# ---- 获取骑手位置 ----
@router.get("/{order_id}/rider-location")
def get_rider_location(
    order_id: int,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    order = db.query(CombinedOrder).filter(
        CombinedOrder.id == order_id,
        CombinedOrder.user_id == user.id,
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
        "phone": mask_phone(rider.phone),
    }


# ---- 取消总单 ----
@router.put("/{order_id}/cancel", response_model=CombinedOrderOut)
def cancel_order(
    order_id: int,
    reason: str = Query(default=""),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    order = db.query(CombinedOrder).filter(
        CombinedOrder.id == order_id,
        CombinedOrder.user_id == user.id,
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status not in ("pending_pay",):
        raise HTTPException(status_code=400, detail="当前状态不可取消")

    order.status = "cancelled"
    for sub in order.sub_orders:
        sub.status = "cancelled"
        sub.cancel_reason = reason or "用户取消"
        sub.cancel_by = "user"
        _add_sub_timeline(sub.id, "cancelled", f"用户取消: {reason or '无理由'}", db)
    db.commit()
    db.refresh(order)

    merchant_ids = {sub.store.user_id for sub in order.sub_orders if sub.store}
    summary = _combined_order_out(order)
    for mid in merchant_ids:
        manager.push_order_event_sync("order_cancelled", summary, merchant_user_id=mid)

    result = CombinedOrderOut.model_validate(order)
    result.sub_orders = [SubOrderOut.model_validate(s) for s in (order.sub_orders or [])]
    for so in result.sub_orders:
        so.store_name = so.store_name_snapshot
    return result


# ---- 取消单个子单 ----
@router.put("/sub/{sub_id}/cancel", response_model=SubOrderOut)
def cancel_sub_order(
    sub_id: int,
    reason: str = Query(default=""),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    sub = db.query(SubOrder).filter(SubOrder.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="子单不存在")
    if sub.combined_order.user_id != user.id:
        raise HTTPException(status_code=404, detail="子单不存在")
    if sub.status not in ("pending_accept",):
        raise HTTPException(status_code=400, detail="当前状态不可退款")

    sub.status = "cancelled"
    sub.cancel_reason = reason or "用户申请退款"
    sub.cancel_by = "user"
    _add_sub_timeline(sub.id, "cancelled", f"用户退款子单: {reason or '无理由'}", db)

    order = sub.combined_order
    order.status = _derive_combined_status(order.sub_orders)
    db.commit()
    db.refresh(sub)

    if sub.store:
        manager.push_order_event_sync("sub_order_cancelled", {"sub_order_id": sub.id}, merchant_user_id=sub.store.user_id)

    result = SubOrderOut.model_validate(sub)
    result.store_name = sub.store.name if sub.store else ""
    return result


# ---- 子单评价 ----
@router.post("/sub/{sub_id}/review", response_model=ReviewOut)
def create_review(
    sub_id: int,
    body: ReviewCreate,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    sub = db.query(SubOrder).filter(SubOrder.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="子单不存在")
    if sub.combined_order.user_id != user.id:
        raise HTTPException(status_code=404, detail="子单不存在")
    if sub.status != "completed":
        raise HTTPException(status_code=400, detail="子单未完成，无法评价")

    existing = db.query(OrderReview).filter(OrderReview.sub_order_id == sub_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="已评价过该子单")

    review = OrderReview(
        sub_order_id=sub_id,
        user_id=user.id,
        score=body.score,
        content=body.content,
        tags=body.tags,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


# ---- 订单修改申请 ----
@router.post("/sub/{sub_id}/request-modification", response_model=ModificationOut)
def request_sub_modification(
    sub_id: int,
    body: ModificationCreate,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """用户申请修改子单（退单/退款等），需要商家审核"""
    sub = db.query(SubOrder).filter(SubOrder.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="子单不存在")
    order = sub.combined_order
    if not order or order.user_id != user.id:
        raise HTTPException(status_code=404, detail="子单不存在")
    if sub.status in ("cancelled", "completed"):
        raise HTTPException(status_code=400, detail="当前状态不可申请修改")

    # 检查是否已有待审核的申请
    existing = db.query(OrderModification).filter(
        OrderModification.sub_order_id == sub_id,
        OrderModification.status == "pending_review",
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="已有待审核的申请，请耐心等待")

    mod = OrderModification(
        combined_order_id=order.id,
        sub_order_id=sub_id,
        type=body.type,
        reason=body.reason,
        status="pending_review",
    )
    db.add(mod)
    _add_sub_timeline(sub_id, "mod_requested", f"用户申请{body.type}: {body.reason}", db)
    db.commit()
    db.refresh(mod)

    # 通知商家
    if sub.store:
        manager.push_order_event_sync(
            "modification_requested",
            {"modification_id": mod.id, "sub_order_id": sub_id, "type": body.type},
            merchant_user_id=sub.store.user_id,
        )

    result = ModificationOut.model_validate(mod)
    result.order_no = order.order_no
    result.store_name = sub.store.name if sub.store else ""
    result.user_name = user.nickname or ""
    return result


@router.post("/{order_id}/request-modification", response_model=ModificationOut)
def request_order_modification(
    order_id: int,
    body: ModificationCreate,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """用户申请修改总单（改地址等），需要商家审核"""
    order = db.query(CombinedOrder).filter(
        CombinedOrder.id == order_id,
        CombinedOrder.user_id == user.id,
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status in ("cancelled", "completed"):
        raise HTTPException(status_code=400, detail="当前状态不可申请修改")

    # 检查是否已有待审核的申请
    existing = db.query(OrderModification).filter(
        OrderModification.combined_order_id == order_id,
        OrderModification.sub_order_id.is_(None),
        OrderModification.status == "pending_review",
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="已有待审核的申请，请耐心等待")

    mod = OrderModification(
        combined_order_id=order.id,
        type=body.type,
        reason=body.reason,
        new_address=body.new_address,
        status="pending_review",
    )
    db.add(mod)
    db.commit()
    db.refresh(mod)

    # 通知所有子单的商家
    merchant_ids = {sub.store.user_id for sub in order.sub_orders if sub.store}
    for mid in merchant_ids:
        manager.push_order_event_sync(
            "modification_requested",
            {"modification_id": mod.id, "order_id": order_id, "type": body.type},
            merchant_user_id=mid,
        )

    result = ModificationOut.model_validate(mod)
    result.order_no = order.order_no
    result.user_name = user.nickname or ""
    return result


@router.get("/{order_id}/modifications", response_model=List[ModificationOut])
def list_order_modifications(
    order_id: int,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """查看订单的修改申请记录"""
    order = db.query(CombinedOrder).filter(
        CombinedOrder.id == order_id,
        CombinedOrder.user_id == user.id,
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    mods = db.query(OrderModification).filter(
        OrderModification.combined_order_id == order_id,
    ).order_by(OrderModification.created_at.desc()).all()

    results = []
    for m in mods:
        r = ModificationOut.model_validate(m)
        r.order_no = order.order_no
        if m.sub_order_id:
            sub = next((s for s in order.sub_orders if s.id == m.sub_order_id), None)
            r.store_name = sub.store.name if sub and sub.store else ""
        results.append(r)
    return results


# ---- 订单留言 ----
@router.get("/{order_id}/messages", response_model=List[OrderMessageOut])
def get_order_messages(
    order_id: int,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """查看订单留言"""
    order = db.query(CombinedOrder).filter(
        CombinedOrder.id == order_id,
        CombinedOrder.user_id == user.id,
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
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """用户发送留言"""
    order = db.query(CombinedOrder).filter(
        CombinedOrder.id == order_id,
        CombinedOrder.user_id == user.id,
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status in ("completed", "cancelled"):
        raise HTTPException(status_code=400, detail="订单已结束，不能留言")

    msg = OrderMessage(
        combined_order_id=order_id,
        sender_id=user.id,
        sender_role="user",
        content=body.content,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    # WebSocket 推送给骑手
    if order.rider_id:
        rider = db.query(Rider).filter(Rider.id == order.rider_id).first()
        if rider:
            manager.push_order_event_sync(
                "new_message", {
                    "order_id": order_id, "order_no": order.order_no,
                    "sender_role": "user", "content": body.content,
                },
                rider_user_id=rider.user_id,
            )

    return OrderMessageOut.model_validate(msg)
