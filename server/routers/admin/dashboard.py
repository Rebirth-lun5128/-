"""管理后台 API"""
from datetime import date, timedelta
import json

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from auth import require_any_admin, require_super_admin, hash_password
from database import get_db
from utils import mask_phone
from models.user import User
from models.store import Store
from models.rider import Rider
from models.order import Order, CombinedOrder, SubOrder, SubOrderItem, OrderModification, SubOrderTimeline, OrderMessage
from models.district import District
from models.region import SystemConfig
from models.coupon import Coupon, UserCoupon
from websocket import manager
from schemas.store import StoreUpdate, DistrictUpdate

router = APIRouter(prefix="/api/admin", tags=["管理后台"])


@router.get("/dashboard")
def dashboard(user: User = Depends(require_any_admin), db: Session = Depends(get_db)):
    today = date.today()

    district_id = user.district_id if user.role == "district_admin" else None
    district_filter = [Order.district_id == district_id] if district_id else []

    total_users = db.query(func.count(User.id)).filter(User.role == "user").scalar() or 0
    total_stores = db.query(func.count(Store.id)).scalar() or 0
    verified_stores = db.query(func.count(Store.id)).filter(Store.verify_status == "verified").scalar() or 0
    total_riders = db.query(func.count(Rider.id)).scalar() or 0
    total_admins = db.query(func.count(User.id)).filter(
        User.role.in_(["district_admin", "super_admin"])
    ).scalar() or 0

    today_orders = db.query(func.count(Order.id)).filter(
        func.date(Order.created_at) == today,
        *district_filter,
    ).scalar() or 0

    today_revenue = db.query(func.coalesce(func.sum(Order.total_price), 0)).filter(
        func.date(Order.created_at) == today,
        Order.status.in_(["completed", "delivered"]),
        *district_filter,
    ).scalar() or 0

    config = db.query(SystemConfig).filter(SystemConfig.config_key == "platform_fee_rate").first()
    fee_rate = float(config.config_value) if config else 0.15
    today_fee = float(today_revenue) * fee_rate

    pending_verify = db.query(func.count(Store.id)).filter(
        Store.verify_status == "unverified"
    ).scalar() or 0
    pending_orders = db.query(func.count(Order.id)).filter(
        Order.status.in_(["pending_accept", "preparing", "ready", "delivering"]),
        *district_filter,
    ).scalar() or 0

    pending_modifications = db.query(func.count(OrderModification.id)).filter(
        OrderModification.status == "pending_review",
    ).scalar() or 0

    today_key = f"visit:{today}"
    visit_config = db.query(SystemConfig).filter(SystemConfig.config_key == today_key).first()
    today_visits = int(visit_config.config_value) if visit_config else 0

    return {
        "total_users": total_users,
        "total_merchants": total_stores,
        "total_stores": total_stores,  # 兼容旧字段
        "verified_merchants": verified_stores,
        "verified_stores": verified_stores,  # 兼容旧字段
        "total_riders": total_riders,
        "total_admins": total_admins,
        "today_orders": today_orders,
        "today_revenue": float(today_revenue),
        "today_platform_fee": round(today_fee, 2),
        "fee_rate": fee_rate,
        "pending_verify_merchants": pending_verify,
        "pending_verify_stores": pending_verify,  # 兼容旧字段
        "pending_orders": pending_orders,
        "pending_modifications": pending_modifications,
        "today_visits": today_visits,
    }


# ---- 店铺管理 ----
@router.get("/stores")
def list_stores(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    verify_status: str = Query(default=""),
    store_type: str = Query(default=""),
    keyword: str = Query(default=""),
    user: User = Depends(require_any_admin),
    db: Session = Depends(get_db),
):
    query = db.query(Store)
    if verify_status:
        query = query.filter(Store.verify_status == verify_status)
    if store_type:
        query = query.filter(Store.store_type == store_type)
    if keyword:
        query = query.filter(Store.name.contains(keyword))
    if user.role == "district_admin" and user.district_id:
        query = query.filter(Store.district_id == user.district_id)

    total = query.count()
    items = query.order_by(Store.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()
    return {
        "total": total,
        "items": [
            {
                "id": r.id, "name": r.name, "phone": mask_phone(r.phone),
                "store_type": r.store_type, "address": r.address,
                "stall_location": r.stall_location, "category": r.category,
                "rating": float(r.rating), "status": r.status,
                "verify_status": r.verify_status, "verify_method": r.verify_method,
                "verify_note": r.verify_note, "created_at": str(r.created_at),
                "commission_rate": float(r.commission_rate or 0.12),
                "delivery_surcharge": float(r.delivery_surcharge or 0),
                "district_id": r.district_id,
                "district_name": r.district.name if r.district else "",
                "combinable_districts": r.combinable_districts or [],
            }
            for r in items
        ],
    }


@router.put("/stores/{store_id}/verify")
def verify_store(
    store_id: int,
    verify_status: str = Query(..., description="verified | rejected"),
    verify_method: str = Query(default="现场核验"),
    verify_note: str = Query(default=""),
    user: User = Depends(require_any_admin),
    db: Session = Depends(get_db),
):
    if verify_status not in ("verified", "rejected"):
        raise HTTPException(status_code=400, detail="无效核验状态")

    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="店铺不存在")
    # 分区管理员只能操作自己分区
    if user.role == "district_admin" and store.district_id != user.district_id:
        raise HTTPException(status_code=403, detail="无权操作其他分区的店铺")

    store.verify_status = verify_status
    store.verify_method = verify_method
    store.verify_note = verify_note
    if verify_status == "verified":
        store.status = "open"
    db.commit()
    return {"message": f"核验{verify_status}", "method": verify_method}


@router.put("/stores/{store_id}")
def update_store(
    store_id: int,
    body: StoreUpdate,
    user: User = Depends(require_any_admin),
    db: Session = Depends(get_db),
):
    """更新店铺设置（分区、跨区合单等）"""
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="店铺不存在")
    # 分区管理员只能编辑自己分区
    if user.role == "district_admin" and store.district_id != user.district_id:
        raise HTTPException(status_code=403, detail="无权编辑其他分区的店铺")

    if body.district_id is not None:
        store.district_id = body.district_id
    if body.combinable_districts is not None:
        store.combinable_districts = body.combinable_districts
    if body.store_type is not None:
        store.store_type = body.store_type
    if body.min_price is not None:
        store.min_price = body.min_price
    if body.delivery_time is not None:
        store.delivery_time = body.delivery_time
    if body.notice is not None:
        store.notice = body.notice

    db.commit()
    return {
        "message": "已更新",
        "district_id": store.district_id,
        "combinable_districts": store.combinable_districts,
    }


@router.put("/stores/{store_id}/toggle-status")
def toggle_store_status(
    store_id: int,
    status: str = Query(..., description="open | closed"),
    user: User = Depends(require_any_admin),
    db: Session = Depends(get_db),
):
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="店铺不存在")
    store.status = status
    db.commit()
    return {"message": f"店铺已{status}"}


# ---- 骑手管理 ----
@router.get("/riders")
def list_riders(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    audit_status: str = Query(default=""),
    user: User = Depends(require_any_admin),
    db: Session = Depends(get_db),
):
    query = db.query(Rider)
    if audit_status:
        query = query.filter(Rider.audit_status == audit_status)
    if user.role == "district_admin" and user.district_id:
        query = query.filter(Rider.district_id == user.district_id)

    total = query.count()
    items = query.order_by(Rider.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()
    return {
        "total": total,
        "items": [
            {
                "id": r.id, "real_name": r.real_name, "phone": mask_phone(r.phone),
                "status": r.status, "balance": float(r.balance),
                "total_orders": r.total_orders, "rating": float(r.rating),
                "audit_status": r.audit_status, "created_at": str(r.created_at),
            }
            for r in items
        ],
    }


@router.put("/riders/{rider_id}/audit")
def audit_rider(
    rider_id: int,
    audit_status: str = Query(...),
    user: User = Depends(require_any_admin),
    db: Session = Depends(get_db),
):
    if audit_status not in ("approved", "rejected"):
        raise HTTPException(status_code=400, detail="无效审核状态")
    rider = db.query(Rider).filter(Rider.id == rider_id).first()
    if not rider:
        raise HTTPException(status_code=404, detail="骑手不存在")
    # 分区管理员只能审核自己分区骑手
    if user.role == "district_admin" and rider.district_id != user.district_id:
        raise HTTPException(status_code=403, detail="无权审核其他分区的骑手")
    rider.audit_status = audit_status
    db.commit()
    return {"message": f"审核{audit_status}"}


# ---- 订单管理 ----
@router.get("/orders")
def list_all_orders(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    status: str = Query(default=""),
    keyword: str = Query(default=""),
    user: User = Depends(require_any_admin),
    db: Session = Depends(get_db),
):
    query = db.query(CombinedOrder)
    if status:
        query = query.filter(CombinedOrder.status == status)
    if keyword:
        query = query.filter(CombinedOrder.order_no.contains(keyword))
    if user.role == "district_admin" and user.district_id:
        query = query.filter(CombinedOrder.district_id == user.district_id)

    total = query.count()
    orders = query.order_by(CombinedOrder.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    items = []
    for o in orders:
        sub_orders = db.query(SubOrder).filter(SubOrder.combined_order_id == o.id).all()
        store_names = [s.store_name_snapshot for s in sub_orders if s.store_name_snapshot]
        rider_name = o.rider.real_name if o.rider else ""
        items.append({
            "id": o.id, "order_no": o.order_no, "status": o.status,
            "total_price": float(o.total_price),
            "delivery_fee": float(o.delivery_fee),
            "items_total": float(o.items_total),
            "store_names": store_names,
            "store_count": len(sub_orders),
            "rider_name": rider_name,
            "created_at": str(o.created_at),
        })

    return {"total": total, "items": items}


@router.get("/orders/{order_id}/detail")
def get_order_detail(
    order_id: int,
    user: User = Depends(require_any_admin),
    db: Session = Depends(get_db),
):
    co = db.query(CombinedOrder).filter(CombinedOrder.id == order_id).first()
    if not co:
        raise HTTPException(status_code=404, detail="订单不存在")

    sub_orders = db.query(SubOrder).filter(SubOrder.combined_order_id == co.id).all()
    sub_list = []
    for sub in sub_orders:
        items = db.query(SubOrderItem).filter(SubOrderItem.sub_order_id == sub.id).all()
        timeline = db.query(SubOrderTimeline).filter(
            SubOrderTimeline.sub_order_id == sub.id
        ).order_by(SubOrderTimeline.created_at).all()
        sub_list.append({
            "id": sub.id,
            "store_id": sub.store_id,
            "store_name": sub.store_name_snapshot or "",
            "items_total": float(sub.items_total),
            "commission_rate": float(sub.commission_rate or 0.12),
            "status": sub.status,
            "cancel_reason": sub.cancel_reason,
            "cancel_by": sub.cancel_by,
            "items": [{
                "id": it.id, "name": it.name, "price": float(it.price),
                "quantity": it.quantity, "image": it.image or "",
            } for it in items],
            "timeline": [{
                "status": t.status, "description": t.description,
                "created_at": str(t.created_at),
            } for t in timeline],
        })

    return {
        "id": co.id,
        "order_no": co.order_no,
        "status": co.status,
        "items_total": float(co.items_total),
        "delivery_fee": float(co.delivery_fee),
        "delivery_fee_original": float(co.delivery_fee_original or 0),
        "delivery_fee_discount": float(co.delivery_fee_discount or 0),
        "total_price": float(co.total_price),
        "address_snapshot": co.address_snapshot or {},
        "rider_name": co.rider.real_name if co.rider else "",
        "rider_phone": mask_phone(co.rider.phone) if co.rider else "",
        "created_at": str(co.created_at),
        "paid_at": str(co.paid_at) if co.paid_at else None,
        "delivered_at": str(co.delivered_at) if co.delivered_at else None,
        "sub_orders": sub_list,
    }


@router.put("/orders/{order_id}/force-cancel")
def force_cancel_order(
    order_id: int,
    reason: str = Query(default="平台介入取消"),
    user: User = Depends(require_any_admin),
    db: Session = Depends(get_db),
):
    from models.order import CombinedOrder, SubOrder, SubOrderTimeline
    co = db.query(CombinedOrder).filter(CombinedOrder.id == order_id).first()
    if co:
        co.status = "cancelled"
        sub_orders = db.query(SubOrder).filter(SubOrder.combined_order_id == co.id).all()
        for sub in sub_orders:
            if sub.status != "cancelled":
                sub.status = "cancelled"
                sub.cancel_reason = reason
                sub.cancel_by = "admin"
                db.add(SubOrderTimeline(sub_order_id=sub.id, status="cancelled", description=f"平台介入: {reason}"))
        db.commit()
        summary = {
            "id": co.id, "order_no": co.order_no, "status": co.status,
            "user_id": co.user_id, "total_price": float(co.total_price),
            "cancel_reason": reason,
        }
        manager.push_order_event_sync("order_force_cancelled", summary, user_id=co.user_id)
        return {"message": "订单已取消"}

    # 兼容旧 Order 模型
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    from models.order import OrderTimeline
    order.status = "cancelled"
    order.cancel_reason = reason
    order.cancel_by = "admin"
    db.add(OrderTimeline(order_id=order.id, status="cancelled", description=f"平台介入: {reason}"))
    db.commit()
    merchant_uid = order.store.user_id if order.store else None
    summary = {
        "id": order.id, "order_no": order.order_no, "status": order.status,
        "user_id": order.user_id, "store_id": order.store_id,
        "rider_id": order.rider_id, "total_price": float(order.total_price),
        "store_name": order.store.name if order.store else "",
        "cancel_reason": reason,
    }
    manager.push_order_event_sync("order_force_cancelled", summary, user_id=order.user_id, merchant_user_id=merchant_uid)
    return {"message": "订单已取消"}


# ---- 财务总览 ----
@router.get("/finance")
def finance_overview(
    user: User = Depends(require_any_admin),
    db: Session = Depends(get_db),
):
    today = date.today()

    district_id = user.district_id if user.role == "district_admin" else None
    district_filter = [Order.district_id == district_id] if district_id else []

    today_total = db.query(func.coalesce(func.sum(Order.total_price), 0)).filter(
        func.date(Order.created_at) == today,
        Order.status.in_(["completed", "delivered"]),
        *district_filter,
    ).scalar() or 0

    today_count = db.query(func.count(Order.id)).filter(
        func.date(Order.created_at) == today,
        Order.status.in_(["completed", "delivered"]),
        *district_filter,
    ).scalar() or 0

    month_start = date.today().replace(day=1)
    month_total = db.query(func.coalesce(func.sum(Order.total_price), 0)).filter(
        func.date(Order.created_at) >= month_start,
        Order.status.in_(["completed", "delivered"]),
        *district_filter,
    ).scalar() or 0

    config = db.query(SystemConfig).filter(SystemConfig.config_key == "platform_fee_rate").first()
    fee_rate = float(config.config_value) if config else 0.15

    return {
        "today_revenue": float(today_total),
        "today_orders": today_count,
        "today_platform_fee": round(float(today_total) * fee_rate, 2),
        "month_revenue": float(month_total),
        "month_platform_fee": round(float(month_total) * fee_rate, 2),
        "fee_rate": fee_rate,
    }


# ---- 分区管理 ----
@router.get("/districts")
def list_districts(user: User = Depends(require_any_admin), db: Session = Depends(get_db)):
    districts = db.query(District).order_by(District.id).all()
    return [
        {"id": d.id, "name": d.name, "admin_id": d.admin_id,
         "coverage": d.coverage, "delivery_fee": d.delivery_fee,
         "peak_delivery_fee": d.peak_delivery_fee,
         "peak_start_hour": d.peak_start_hour,
         "peak_end_hour": d.peak_end_hour,
         "delivery_fee_rules": d.delivery_fee_rules or [],
         "delivery_range": d.delivery_range, "notice": d.notice}
        for d in districts
    ]


@router.post("/districts")
def create_district(
    name: str = Query(...),
    coverage: str = Query(default="[]"),
    delivery_fee: int = Query(default=0),
    delivery_range: int = Query(default=3),
    notice: str = Query(default=""),
    user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    district = District(
        name=name,
        coverage=json.loads(coverage) if coverage else [],
        delivery_fee=delivery_fee,
        delivery_range=delivery_range,
        notice=notice,
    )
    db.add(district)
    db.commit()
    db.refresh(district)
    return {"message": "分区已创建", "id": district.id}


@router.put("/districts/{district_id}")
def update_district(
    district_id: int,
    body: DistrictUpdate,
    user: User = Depends(require_any_admin),
    db: Session = Depends(get_db),
):
    district = db.query(District).filter(District.id == district_id).first()
    if not district:
        raise HTTPException(status_code=404, detail="分区不存在")
    if body.name is not None:
        district.name = body.name
    if body.coverage is not None:
        district.coverage = json.loads(body.coverage) if body.coverage else []
    if body.delivery_fee is not None:
        district.delivery_fee = body.delivery_fee
    if body.delivery_range is not None:
        district.delivery_range = body.delivery_range
    if body.notice is not None:
        district.notice = body.notice
    if body.admin_id is not None:
        district.admin_id = body.admin_id
    if body.status is not None:
        district.status = body.status
    db.commit()
    return {"message": "分区已更新"}


# ---- 系统配置 ----
@router.get("/system/configs")
def get_configs(user: User = Depends(require_super_admin), db: Session = Depends(get_db)):
    configs = db.query(SystemConfig).all()
    return [
        {"key": c.config_key, "value": c.config_value, "description": c.description}
        for c in configs
    ]


@router.put("/system/configs/{key}")
def update_config(
    key: str,
    value: str,
    user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    config = db.query(SystemConfig).filter(SystemConfig.config_key == key).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置项不存在")
    config.config_value = value
    db.commit()
    return {"message": "已更新"}


# ---- 管理员管理 ----
@router.get("/admins")
def list_admins(user: User = Depends(require_super_admin), db: Session = Depends(get_db)):
    admins = db.query(User).filter(
        User.role.in_(["super_admin", "district_admin"])
    ).order_by(User.created_at.desc()).all()
    return [
        {"id": a.id, "nickname": a.nickname, "phone": mask_phone(a.phone),
         "role": a.role, "district_id": a.district_id, "status": a.status,
         "created_at": str(a.created_at)}
        for a in admins
    ]


@router.post("/admins")
def create_admin(
    phone: str = Body(...),
    password: str = Body(...),
    nickname: str = Body(default="管理员"),
    role: str = Body(default="district_admin"),
    district_id: int = Body(default=None),
    user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    if role not in ("district_admin", "super_admin"):
        raise HTTPException(status_code=400, detail="无效角色")
    existing = db.query(User).filter(User.phone == phone).first()
    if existing:
        raise HTTPException(status_code=400, detail="手机号已存在")
    admin = User(
        openid=f"admin_{phone}",
        nickname=nickname,
        phone=phone,
        role=role,
        district_id=district_id,
        hashed_password=hash_password(password),
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return {"message": "管理员已创建", "id": admin.id}


@router.put("/admins/{user_id}/toggle-status")
def toggle_admin_status(
    user_id: int,
    user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    admin = db.query(User).filter(User.id == user_id, User.role.in_(["super_admin", "district_admin"])).first()
    if not admin:
        raise HTTPException(status_code=404, detail="管理员不存在")
    admin.status = 0 if admin.status == 1 else 1
    db.commit()
    return {"message": f"已{'启用' if admin.status == 1 else '禁用'}"}


@router.put("/admins/{user_id}")
def update_admin(
    user_id: int,
    nickname: str = Body(default=None),
    district_id: int = Body(default=None),
    password: str = Body(default=None),
    user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """编辑管理员信息"""
    admin = db.query(User).filter(
        User.id == user_id, User.role.in_(["super_admin", "district_admin"])
    ).first()
    if not admin:
        raise HTTPException(status_code=404, detail="管理员不存在")
    if nickname is not None:
        admin.nickname = nickname
    if district_id is not None:
        admin.district_id = district_id
    if password:
        admin.hashed_password = hash_password(password)
    db.commit()
    return {"message": "已更新"}


@router.delete("/admins/{user_id}")
def delete_admin(
    user_id: int,
    user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """删除管理员"""
    admin = db.query(User).filter(
        User.id == user_id, User.role.in_(["super_admin", "district_admin"])
    ).first()
    if not admin:
        raise HTTPException(status_code=404, detail="管理员不存在")
    db.delete(admin)
    db.commit()
    return {"message": "已删除"}


# ---- 订单统计 ----
@router.get("/orders/stats")
def order_stats(
    days: int = Query(default=7, le=90),
    user: User = Depends(require_any_admin),
    db: Session = Depends(get_db),
):
    result = []
    for i in range(days - 1, -1, -1):
        d = date.today() - timedelta(days=i)
        district_filter = [Order.district_id == user.district_id] if user.role == "district_admin" and user.district_id else []
        count = db.query(func.count(Order.id)).filter(
            func.date(Order.created_at) == d,
            Order.status.in_(["completed", "delivered"]),
            *district_filter,
        ).scalar() or 0
        revenue = db.query(func.coalesce(func.sum(Order.total_price), 0)).filter(
            func.date(Order.created_at) == d,
            Order.status.in_(["completed", "delivered"]),
            *district_filter,
        ).scalar() or 0
        result.append({"date": str(d), "count": count, "revenue": round(float(revenue), 2)})
    return result


# ---- 商家抽成 & 附加费管理 ----
@router.put("/stores/{store_id}/commission-rate")
def set_store_commission_rate(
    store_id: int,
    rate: float = Query(..., ge=0, le=1, description="抽成比例 0~1"),
    user: User = Depends(require_any_admin),
    db: Session = Depends(get_db),
):
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="店铺不存在")
    store.commission_rate = rate
    db.commit()
    return {"message": f"抽成比例已设为 {rate}", "commission_rate": rate}


@router.put("/stores/{store_id}/delivery-surcharge")
def set_store_delivery_surcharge(
    store_id: int,
    surcharge: float = Query(..., ge=0, description="配送附加费(元)"),
    user: User = Depends(require_any_admin),
    db: Session = Depends(get_db),
):
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="店铺不存在")
    store.delivery_surcharge = surcharge
    db.commit()
    return {"message": f"配送附加费已设为 ¥{surcharge}", "delivery_surcharge": surcharge}


# ---- 店铺二维码 ----

@router.get("/stores/{store_id}/qrcode")
def get_store_qrcode(store_id: int, user: User = Depends(require_any_admin), db: Session = Depends(get_db)):
    """获取店铺二维码信息"""
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="店铺不存在")
    content = {"store_id": store.id, "name": store.name,
               "path": f"pages/restaurant/restaurant?id={store.id}"}
    return {
        "store_id": store.id,
        "store_name": store.name,
        "qr_code": store.qr_code or "",
        "content": content,
    }


@router.post("/stores/{store_id}/qrcode")
def generate_store_qrcode(store_id: int, user: User = Depends(require_any_admin), db: Session = Depends(get_db)):
    """生成/重新生成店铺二维码"""
    import json
    import uuid
    import qrcode
    from config import settings

    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="店铺不存在")

    content = {"store_id": store.id, "name": store.name,
               "path": f"pages/restaurant/restaurant?id={store.id}"}
    content_str = json.dumps(content, ensure_ascii=False)

    # 生成 QR 码
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(content_str)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # 保存到 uploads 目录
    import os
    from pathlib import Path
    filename = f"qr_store_{store.id}_{uuid.uuid4().hex[:8]}.png"
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    filepath = upload_dir / filename
    img.save(str(filepath), "PNG")

    # 更新数据库
    store.qr_code = f"/uploads/{filename}"
    db.commit()

    return {
        "store_id": store.id,
        "store_name": store.name,
        "qr_code": store.qr_code,
        "content": content,
    }


# ---- 分区配送费高级设置 ----
@router.put("/districts/{district_id}/delivery-fee-settings")
def set_district_delivery_fee(
    district_id: int,
    base_fee: int = Query(default=None, description="基础配送费(分)"),
    peak_fee: int = Query(default=None, description="高峰期配送费(分)"),
    peak_start_hour: int = Query(default=None, description="高峰期开始小时"),
    peak_end_hour: int = Query(default=None, description="高峰期结束小时"),
    user: User = Depends(require_any_admin),
    db: Session = Depends(get_db),
):
    district = db.query(District).filter(District.id == district_id).first()
    if not district:
        raise HTTPException(status_code=404, detail="分区不存在")
    if base_fee is not None:
        district.delivery_fee = base_fee
    if peak_fee is not None:
        district.peak_delivery_fee = peak_fee
    if peak_start_hour is not None:
        district.peak_start_hour = peak_start_hour
    if peak_end_hour is not None:
        district.peak_end_hour = peak_end_hour
    db.commit()
    return {
        "message": "配送费设置已更新",
        "delivery_fee": district.delivery_fee,
        "peak_delivery_fee": district.peak_delivery_fee,
        "peak_start_hour": district.peak_start_hour,
        "peak_end_hour": district.peak_end_hour,
    }


@router.put("/districts/{district_id}/delivery-rules")
def set_district_delivery_rules(
    district_id: int,
    rules: list = Body(..., description="满减配送费规则列表"),
    user: User = Depends(require_any_admin),
    db: Session = Depends(get_db),
):
    district = db.query(District).filter(District.id == district_id).first()
    if not district:
        raise HTTPException(status_code=404, detail="分区不存在")
    district.delivery_fee_rules = rules
    db.commit()
    return {"message": "满减配送费规则已更新", "delivery_fee_rules": rules}


# ---- 优惠券管理 ----
@router.get("/coupons")
def list_coupons(
    user: User = Depends(require_any_admin),
    db: Session = Depends(get_db),
):
    query = db.query(Coupon)
    if user.role == "district_admin":
        query = query.filter(
            (Coupon.district_id == user.district_id) | (Coupon.district_id == None)
        )
    coupons = query.order_by(Coupon.created_at.desc()).all()
    return [
        {
            "id": c.id, "name": c.name, "coupon_type": c.coupon_type,
            "condition_amount": float(c.condition_amount), "discount_amount": float(c.discount_amount),
            "total_count": c.total_count, "used_count": c.used_count,
            "district_id": c.district_id, "store_id": c.store_id,
            "start_time": str(c.start_time) if c.start_time else None,
            "end_time": str(c.end_time) if c.end_time else None,
            "status": c.status, "created_at": str(c.created_at),
        }
        for c in coupons
    ]


@router.post("/coupons")
def create_coupon(
    name: str = Query(...),
    coupon_type: str = Query(...),
    discount_amount: float = Query(...),
    condition_amount: float = Query(default=0),
    total_count: int = Query(default=0),
    district_id: int = Query(default=None),
    store_id: int = Query(default=None),
    start_time: str = Query(default=None),
    end_time: str = Query(default=None),
    user: User = Depends(require_any_admin),
    db: Session = Depends(get_db),
):
    if coupon_type not in ("new_user", "full_reduction", "direct_discount"):
        raise HTTPException(status_code=400, detail="无效的优惠券类型")
    coupon = Coupon(
        name=name, coupon_type=coupon_type,
        condition_amount=condition_amount, discount_amount=discount_amount,
        total_count=total_count, district_id=district_id, store_id=store_id,
        start_time=start_time, end_time=end_time,
    )
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    return {"message": "优惠券已创建", "id": coupon.id}


@router.put("/coupons/{coupon_id}")
def update_coupon(
    coupon_id: int,
    name: str = Query(default=None),
    condition_amount: float = Query(default=None),
    discount_amount: float = Query(default=None),
    total_count: int = Query(default=None),
    start_time: str = Query(default=None),
    end_time: str = Query(default=None),
    user: User = Depends(require_any_admin),
    db: Session = Depends(get_db),
):
    coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="优惠券不存在")
    if name is not None: coupon.name = name
    if condition_amount is not None: coupon.condition_amount = condition_amount
    if discount_amount is not None: coupon.discount_amount = discount_amount
    if total_count is not None: coupon.total_count = total_count
    if start_time is not None: coupon.start_time = start_time
    if end_time is not None: coupon.end_time = end_time
    db.commit()
    return {"message": "已更新"}


@router.put("/coupons/{coupon_id}/toggle")
def toggle_coupon(
    coupon_id: int,
    user: User = Depends(require_any_admin),
    db: Session = Depends(get_db),
):
    coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="优惠券不存在")
    coupon.status = 0 if coupon.status == 1 else 1
    db.commit()
    return {"message": "已启用" if coupon.status == 1 else "已停用", "status": coupon.status}


# ---- 订单修改审核（管理端） ----
@router.get("/orders/modifications")
def admin_list_modifications(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    status: str = Query(default=""),
    user: User = Depends(require_any_admin),
    db: Session = Depends(get_db),
):
    """管理端查看所有修改申请"""
    query = db.query(OrderModification)
    if status:
        query = query.filter(OrderModification.status == status)

    total = query.count()
    items = query.order_by(OrderModification.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    results = []
    for m in items:
        order = db.query(CombinedOrder).filter(CombinedOrder.id == m.combined_order_id).first()
        store_name = ""
        if m.sub_order_id:
            sub = db.query(SubOrder).filter(SubOrder.id == m.sub_order_id).first()
            store_name = sub.store.name if sub and sub.store else ""
        user_name = order.user.nickname if order and order.user else ""
        results.append({
            "id": m.id, "combined_order_id": m.combined_order_id,
            "sub_order_id": m.sub_order_id, "type": m.type,
            "reason": m.reason, "new_address": m.new_address,
            "status": m.status, "reviewed_by": m.reviewed_by,
            "review_comment": m.review_comment,
            "reviewed_at": str(m.reviewed_at) if m.reviewed_at else None,
            "created_at": str(m.created_at),
            "order_no": order.order_no if order else "",
            "store_name": store_name,
            "user_name": user_name,
            "items_total": float(sub.items_total) if m.sub_order_id and (sub := db.query(SubOrder).filter(SubOrder.id == m.sub_order_id).first()) else 0,
        })

    return {"total": total, "items": results}


@router.put("/orders/modifications/{mod_id}/approve")
def admin_approve_modification(
    mod_id: int,
    comment: str = Query(default="平台审核通过"),
    user: User = Depends(require_any_admin),
    db: Session = Depends(get_db),
):
    """管理端同意修改申请"""
    mod = db.query(OrderModification).filter(OrderModification.id == mod_id).first()
    if not mod:
        raise HTTPException(status_code=404, detail="申请不存在")
    if mod.status != "pending_review":
        raise HTTPException(status_code=400, detail="申请已处理")

    from datetime import datetime as dt

    mod.status = "approved"
    mod.reviewed_by = user.id
    mod.review_comment = comment
    mod.reviewed_at = dt.now()

    if mod.type in ("cancel", "refund") and mod.sub_order_id:
        sub = db.query(SubOrder).filter(SubOrder.id == mod.sub_order_id).first()
        if sub:
            sub.status = "cancelled"
            sub.cancel_reason = mod.reason or "用户申请退单(管理员同意)"
            sub.cancel_by = "user"
            db.add(SubOrderTimeline(sub_order_id=sub.id, status="cancelled", description=f"管理员同意退单: {mod.reason}"))
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

    db.commit()
    db.refresh(mod)

    order = db.query(CombinedOrder).filter(CombinedOrder.id == mod.combined_order_id).first()
    if order:
        manager.push_order_event_sync(
            "modification_approved",
            {"modification_id": mod.id, "type": mod.type, "status": "approved"},
            user_id=order.user_id,
        )

    return {"message": "已同意修改申请", "modification_id": mod.id}


@router.put("/orders/modifications/{mod_id}/reject")
def admin_reject_modification(
    mod_id: int,
    comment: str = Query(default="平台审核不通过"),
    user: User = Depends(require_any_admin),
    db: Session = Depends(get_db),
):
    """管理端拒绝修改申请"""
    mod = db.query(OrderModification).filter(OrderModification.id == mod_id).first()
    if not mod:
        raise HTTPException(status_code=404, detail="申请不存在")
    if mod.status != "pending_review":
        raise HTTPException(status_code=400, detail="申请已处理")

    from datetime import datetime as dt

    mod.status = "rejected"
    mod.reviewed_by = user.id
    mod.review_comment = comment
    mod.reviewed_at = dt.now()

    if mod.sub_order_id:
        db.add(SubOrderTimeline(sub_order_id=mod.sub_order_id, status="mod_rejected", description=f"管理员拒绝申请: {comment}"))

    db.commit()
    db.refresh(mod)

    order = db.query(CombinedOrder).filter(CombinedOrder.id == mod.combined_order_id).first()
    if order:
        manager.push_order_event_sync(
            "modification_rejected",
            {"modification_id": mod.id, "type": mod.type, "status": "rejected"},
            user_id=order.user_id,
        )

    return {"message": "已拒绝修改申请", "modification_id": mod.id}


# ---- 访问统计 ----
@router.post("/visits/track")
def track_visit(
    page: str = Query(default=""),
    db: Session = Depends(get_db),
):
    """记录一次管理后台页面访问"""
    today_key = f"visit:{date.today()}"
    config = db.query(SystemConfig).filter(SystemConfig.config_key == today_key).first()
    if config:
        config.config_value = str(int(config.config_value) + 1)
    else:
        config = SystemConfig(config_key=today_key, config_value="1", description="每日访问量")
        db.add(config)
    db.commit()
    return {"message": "ok"}


@router.get("/visits/stats")
def visit_stats(days: int = Query(default=7, le=30), db: Session = Depends(get_db)):
    """获取近期访问量统计"""
    result = []
    total = 0
    for i in range(days - 1, -1, -1):
        d = date.today() - timedelta(days=i)
        key = f"visit:{d}"
        config = db.query(SystemConfig).filter(SystemConfig.config_key == key).first()
        count = int(config.config_value) if config else 0
        total += count
        result.append({"date": str(d), "count": count})

    today_key = f"visit:{date.today()}"
    today_config = db.query(SystemConfig).filter(SystemConfig.config_key == today_key).first()
    today_count = int(today_config.config_value) if today_config else 0

    yesterday = date.today() - timedelta(days=1)
    yesterday_key = f"visit:{yesterday}"
    yesterday_config = db.query(SystemConfig).filter(SystemConfig.config_key == yesterday_key).first()
    yesterday_count = int(yesterday_config.config_value) if yesterday_config else 0

    return {
        "today": today_count,
        "yesterday": yesterday_count,
        "total": total,
        "daily": result,
    }


# ---- 结算审批 ----
@router.get("/settlements")
def list_settlements(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    status: str = Query(default=""),
    target_type: str = Query(default=""),
    user: User = Depends(require_any_admin),
    db: Session = Depends(get_db),
):
    """管理员查看结算申请列表"""
    from models.region import Settlement
    query = db.query(Settlement)
    if status:
        query = query.filter(Settlement.status == status)
    if target_type:
        query = query.filter(Settlement.target_type == target_type)

    total = query.count()
    items = query.order_by(Settlement.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    result_items = []
    for s in items:
        target_name = ""
        target_phone = ""
        if s.target_type == "rider":
            rider = db.query(Rider).filter(Rider.id == s.target_id).first()
            if rider:
                target_name = rider.real_name
                target_phone = mask_phone(rider.phone) or ""
        elif s.target_type == "store":
            store = db.query(Store).filter(Store.id == s.target_id).first()
            if store:
                target_name = store.name
                target_phone = mask_phone(store.phone) or ""

        result_items.append({
            "id": s.id,
            "target_type": s.target_type,
            "target_id": s.target_id,
            "target_name": target_name,
            "target_phone": target_phone,
            "amount": float(s.amount),
            "net_amount": float(s.net_amount),
            "fee": float(s.fee),
            "status": s.status,
            "period": s.period,
            "created_at": str(s.created_at),
            "paid_at": str(s.paid_at) if s.paid_at else None,
        })

    return {"total": total, "items": result_items}


@router.put("/settlements/{settlement_id}/approve")
def approve_settlement(
    settlement_id: int,
    user: User = Depends(require_any_admin),
    db: Session = Depends(get_db),
):
    """管理员确认结算（已线下打款），扣减骑手/商家余额"""
    from models.region import Settlement
    from datetime import datetime as dt

    settlement = db.query(Settlement).filter(Settlement.id == settlement_id).first()
    if not settlement:
        raise HTTPException(status_code=404, detail="结算申请不存在")
    if settlement.status != "pending":
        raise HTTPException(status_code=400, detail="该申请已处理")

    # 扣减余额
    if settlement.target_type == "rider":
        rider = db.query(Rider).filter(Rider.id == settlement.target_id).first()
        if rider:
            if float(rider.balance) < float(settlement.amount):
                raise HTTPException(status_code=400, detail="骑手余额不足（可能已被其他结算扣减）")
            rider.balance = float(rider.balance) - float(settlement.amount)
    elif settlement.target_type == "store":
        store = db.query(Store).filter(Store.id == settlement.target_id).first()
        if store and hasattr(store, 'balance'):
            if float(store.balance) < float(settlement.amount):
                raise HTTPException(status_code=400, detail="商家余额不足")
            store.balance = float(store.balance) - float(settlement.amount)

    settlement.status = "paid"
    settlement.paid_at = dt.now()
    db.commit()

    return {"message": f"已确认结算 ¥{float(settlement.amount):.2f}", "settlement_id": settlement.id}


# ---- 用户列表 ----
@router.get("/customers")
def list_customers(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    keyword: str = Query(default=""),
    district_id: int = Query(default=None),
    user: User = Depends(require_any_admin),
    db: Session = Depends(get_db),
):
    """列出平台注册用户（可按分区筛选）"""
    query = db.query(User).filter(User.role == "user")
    if keyword:
        query = query.filter(
            User.nickname.contains(keyword) | User.phone.contains(keyword)
        )
    # 分区管理员只能看自己分区
    if user.role == "district_admin":
        query = query.filter(User.district_id == user.district_id)
    elif district_id:
        query = query.filter(User.district_id == district_id)
    total = query.count()
    items = query.order_by(User.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()
    return {
        "total": total,
        "items": [{
            "id": u.id,
            "nickname": u.nickname or "",
            "avatar": u.avatar or "",
            "phone": mask_phone(u.phone) or "",
            "district_id": u.district_id,
            "created_at": str(u.created_at),
        } for u in items],
    }


# ---- 推送通知 ----
@router.get("/notifications")
def list_notifications(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    user: User = Depends(require_any_admin),
    db: Session = Depends(get_db),
):
    """查看已发送的通知"""
    from models.notification import Notification
    query = db.query(Notification)
    if user.role == "district_admin":
        query = query.filter(
            (Notification.district_id == user.district_id) |
            (Notification.district_id == None)
        )
    total = query.count()
    items = query.order_by(Notification.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()
    return {
        "total": total,
        "items": [{
            "id": n.id,
            "title": n.title,
            "content": n.content,
            "district_id": n.district_id,
            "target_role": n.target_role,
            "admin_id": n.admin_id,
            "created_at": str(n.created_at),
        } for n in items],
    }


@router.post("/notifications/send")
async def send_notification(
    title: str = Body(...),
    content: str = Body(default=""),
    target_role: str = Body(default="user"),
    district_id: int = Body(default=None),
    user: User = Depends(require_any_admin),
    db: Session = Depends(get_db),
):
    """发送推送通知"""
    from models.notification import Notification

    if user.role == "district_admin":
        district_id = user.district_id

    notification = Notification(
        title=title,
        content=content,
        district_id=district_id,
        target_role=target_role,
        admin_id=user.id,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)

    # WebSocket 推送给目标用户
    payload = {
        "type": "admin_notification",
        "id": notification.id,
        "title": title,
        "content": content,
    }
    if target_role == "all":
        await manager.broadcast(payload)
    else:
        await manager.send_to_role(target_role, payload)

    return {
        "message": "通知已发送",
        "id": notification.id,
        "target_role": target_role,
        "district_id": district_id,
    }


# ---- 订单留言（只读） ----
@router.get("/orders/{order_id}/messages")
def admin_get_order_messages(
    order_id: int,
    user: User = Depends(require_any_admin),
    db: Session = Depends(get_db),
):
    """管理员查看订单留言"""
    msgs = db.query(OrderMessage).filter(
        OrderMessage.combined_order_id == order_id
    ).order_by(OrderMessage.created_at).all()
    return [{
        "id": m.id,
        "combined_order_id": m.combined_order_id,
        "sender_id": m.sender_id,
        "sender_role": m.sender_role,
        "content": m.content,
        "created_at": str(m.created_at),
    } for m in msgs]


# ---- 佣金阶梯 ----

def _get_tiered_rate(tiers: list, monthly_sales: float) -> float:
    """根据阶梯配置匹配抽成比例，未配置返回 None"""
    if not tiers:
        return None
    for t in tiers:
        t_min = float(t.get("min", 0))
        t_max = float(t.get("max", -1))
        if monthly_sales >= t_min and (t_max < 0 or monthly_sales < t_max):
            return float(t.get("rate", 0))
    return float(tiers[-1].get("rate", 0)) if tiers else None


def get_monthly_store_sales(store_id: int, db: Session) -> float:
    """查询店铺当月累计销售额"""
    from datetime import datetime
    now = datetime.now()
    start = datetime(now.year, now.month, 1)
    result = db.query(func.coalesce(func.sum(SubOrder.items_total), 0)).filter(
        SubOrder.store_id == store_id,
        SubOrder.status.in_(["completed"]),
        SubOrder.updated_at >= start,
    ).scalar()
    return float(result or 0)


@router.get("/commission-tiers")
def get_commission_tiers(user: User = Depends(require_super_admin), db: Session = Depends(get_db)):
    """获取平台和分区佣金阶梯"""
    ct = db.query(SystemConfig).filter(SystemConfig.config_key == "commission_tiers").first()
    dct = db.query(SystemConfig).filter(SystemConfig.config_key == "district_commission_tiers").first()
    return {
        "commission_tiers": json.loads(ct.config_value) if ct else [],
        "district_commission_tiers": json.loads(dct.config_value) if dct else [],
    }


@router.put("/commission-tiers")
def set_commission_tiers(
    tiers: list = Body(...),
    user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """更新平台佣金阶梯"""
    ct = db.query(SystemConfig).filter(SystemConfig.config_key == "commission_tiers").first()
    if ct:
        ct.config_value = json.dumps(tiers)
    else:
        db.add(SystemConfig(config_key="commission_tiers", config_value=json.dumps(tiers),
                           description="平台佣金阶梯配置"))
    db.commit()
    return {"message": "已保存", "commission_tiers": tiers}


@router.put("/commission-tiers/district")
def set_district_commission_tiers(
    tiers: list = Body(...),
    user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """更新分区佣金阶梯"""
    dct = db.query(SystemConfig).filter(SystemConfig.config_key == "district_commission_tiers").first()
    if dct:
        dct.config_value = json.dumps(tiers)
    else:
        db.add(SystemConfig(config_key="district_commission_tiers", config_value=json.dumps(tiers),
                           description="分区管理员佣金阶梯配置"))
    db.commit()
    return {"message": "已保存", "district_commission_tiers": tiers}
