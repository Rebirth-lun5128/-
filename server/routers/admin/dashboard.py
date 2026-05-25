from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from auth import require_any_admin, require_super_admin, hash_password
from database import get_db
from models.user import User
from models.restaurant import Restaurant
from models.rider import Rider
from models.order import Order
from models.region import Region, SystemConfig
from websocket import manager

router = APIRouter(prefix="/api/admin", tags=["管理后台"])


@router.get("/dashboard")
def dashboard(user: User = Depends(require_any_admin), db: Session = Depends(get_db)):
    """数据大盘 — 平台端核心数据"""
    today = date.today()

    region_id = user.region_id if user.role == "region_admin" else None
    region_filter = [Order.region_id == region_id] if region_id else []

    total_users = db.query(func.count(User.id)).filter(User.role == "user").scalar() or 0
    total_merchants = db.query(func.count(Restaurant.id)).scalar() or 0
    verified_merchants = db.query(func.count(Restaurant.id)).filter(
        Restaurant.verify_status == "verified"
    ).scalar() or 0
    total_riders = db.query(func.count(Rider.id)).scalar() or 0

    today_orders = db.query(func.count(Order.id)).filter(
        func.date(Order.created_at) == today,
        *region_filter,
    ).scalar() or 0

    today_revenue = db.query(func.coalesce(func.sum(Order.total_price), 0)).filter(
        func.date(Order.created_at) == today,
        Order.status.in_(["completed", "delivered"]),
        *region_filter,
    ).scalar() or 0

    # 平台抽成 (默认15%)
    config = db.query(SystemConfig).filter(SystemConfig.config_key == "platform_fee_rate").first()
    fee_rate = float(config.config_value) if config else 0.15
    today_fee = float(today_revenue) * fee_rate

    # 待处理
    pending_verify = db.query(func.count(Restaurant.id)).filter(
        Restaurant.verify_status == "unverified"
    ).scalar() or 0
    pending_orders = db.query(func.count(Order.id)).filter(
        Order.status.in_(["pending_accept", "preparing", "ready", "delivering"]),
        *region_filter,
    ).scalar() or 0

    return {
        "total_users": total_users,
        "total_merchants": total_merchants,
        "verified_merchants": verified_merchants,
        "total_riders": total_riders,
        "today_orders": today_orders,
        "today_revenue": float(today_revenue),
        "today_platform_fee": round(today_fee, 2),
        "fee_rate": fee_rate,
        "pending_verify_merchants": pending_verify,
        "pending_orders": pending_orders,
    }


# ---- 商家管理 (适配夜市) ----
@router.get("/restaurants")
def list_restaurants(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    verify_status: str = Query(default=""),
    user: User = Depends(require_any_admin),
    db: Session = Depends(get_db),
):
    query = db.query(Restaurant)
    if verify_status:
        query = query.filter(Restaurant.verify_status == verify_status)
    if user.role == "region_admin" and user.region_id:
        query = query.filter(Restaurant.region_id == user.region_id)

    total = query.count()
    items = query.order_by(Restaurant.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()
    return {
        "total": total,
        "items": [
            {
                "id": r.id,
                "name": r.name,
                "phone": r.phone,
                "address": r.address,
                "stall_location": r.stall_location,
                "category": r.category,
                "rating": float(r.rating),
                "status": r.status,
                "verify_status": r.verify_status,
                "verify_method": r.verify_method,
                "verify_note": r.verify_note,
                "created_at": str(r.created_at),
            }
            for r in items
        ],
    }


@router.put("/restaurants/{restaurant_id}/verify")
def verify_restaurant(
    restaurant_id: int,
    verify_status: str = Query(..., description="verified | rejected"),
    verify_method: str = Query(default="现场核验"),
    verify_note: str = Query(default=""),
    user: User = Depends(require_any_admin),
    db: Session = Depends(get_db),
):
    """
    平台人工核验商家 — 夜市摊主无需营业执照
    核验方式: 现场核验 / 视频核验 / 身份证核验
    """
    if verify_status not in ("verified", "rejected"):
        raise HTTPException(status_code=400, detail="无效核验状态")

    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="餐厅不存在")

    restaurant.verify_status = verify_status
    restaurant.verify_method = verify_method
    restaurant.verify_note = verify_note
    if verify_status == "verified":
        restaurant.status = "open"  # 核验通过自动开业
    db.commit()
    return {"message": f"核验{verify_status}", "method": verify_method}


@router.put("/restaurants/{restaurant_id}/toggle-status")
def toggle_restaurant_status(
    restaurant_id: int,
    status: str = Query(..., description="open | closed"),
    user: User = Depends(require_any_admin),
    db: Session = Depends(get_db),
):
    """平台强制开关店"""
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="餐厅不存在")
    restaurant.status = status
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
    if user.role == "region_admin" and user.region_id:
        query = query.filter(Rider.region_id == user.region_id)

    total = query.count()
    items = query.order_by(Rider.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()
    return {
        "total": total,
        "items": [
            {
                "id": r.id,
                "real_name": r.real_name,
                "phone": r.phone,
                "status": r.status,
                "balance": float(r.balance),
                "total_orders": r.total_orders,
                "rating": float(r.rating),
                "audit_status": r.audit_status,
                "created_at": str(r.created_at),
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
    rider.audit_status = audit_status
    db.commit()
    return {"message": f"审核{audit_status}"}


# ---- 订单管理 ----
@router.get("/orders")
def list_all_orders(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    status: str = Query(default=""),
    user: User = Depends(require_any_admin),
    db: Session = Depends(get_db),
):
    query = db.query(Order)
    if status:
        query = query.filter(Order.status == status)
    if user.role == "region_admin" and user.region_id:
        query = query.filter(Order.region_id == user.region_id)

    total = query.count()
    items = query.order_by(Order.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()
    return {
        "total": total,
        "items": [
            {
                "id": o.id,
                "order_no": o.order_no,
                "status": o.status,
                "total_price": float(o.total_price),
                "delivery_fee": float(o.delivery_fee),
                "restaurant_name": o.restaurant.name if o.restaurant else "",
                "rider_name": o.rider.real_name if o.rider else "",
                "cancel_reason": o.cancel_reason,
                "cancel_by": o.cancel_by,
                "created_at": str(o.created_at),
            }
            for o in items
        ],
    }


@router.put("/orders/{order_id}/force-cancel")
def force_cancel_order(
    order_id: int,
    reason: str = Query(default="平台介入取消"),
    user: User = Depends(require_any_admin),
    db: Session = Depends(get_db),
):
    """平台强制取消订单 (纠纷仲裁)"""
    from models.order import OrderTimeline
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    order.status = "cancelled"
    order.cancel_reason = reason
    order.cancel_by = "admin"
    db.add(OrderTimeline(order_id=order.id, status="cancelled", description=f"平台介入: {reason}"))
    db.commit()
    # 推送通知给用户和商家
    merchant_uid = order.restaurant.user_id if order.restaurant else None
    summary = {
        "id": order.id, "order_no": order.order_no, "status": order.status,
        "user_id": order.user_id, "restaurant_id": order.restaurant_id,
        "rider_id": order.rider_id, "total_price": float(order.total_price),
        "restaurant_name": order.restaurant.name if order.restaurant else "",
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
    """平台财务总览 — 流水、抽成、待结算"""
    today = date.today()

    region_id = user.region_id if user.role == "region_admin" else None
    region_filter = [Order.region_id == region_id] if region_id else []

    # 今日
    today_total = db.query(func.coalesce(func.sum(Order.total_price), 0)).filter(
        func.date(Order.created_at) == today,
        Order.status.in_(["completed", "delivered"]),
        *region_filter,
    ).scalar() or 0

    today_count = db.query(func.count(Order.id)).filter(
        func.date(Order.created_at) == today,
        Order.status.in_(["completed", "delivered"]),
        *region_filter,
    ).scalar() or 0

    # 本月
    month_start = date.today().replace(day=1)
    month_total = db.query(func.coalesce(func.sum(Order.total_price), 0)).filter(
        func.date(Order.created_at) >= month_start,
        Order.status.in_(["completed", "delivered"]),
        *region_filter,
    ).scalar() or 0

    # 平台抽成
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


# ---- 区域管理 ----
@router.get("/regions")
def list_regions(user: User = Depends(require_any_admin), db: Session = Depends(get_db)):
    regions = db.query(Region).filter(Region.status == 1).order_by(Region.sort_order).all()
    return [
        {"id": r.id, "name": r.name, "parent_id": r.parent_id, "manager_id": r.manager_id}
        for r in regions
    ]


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
        User.role.in_(["super_admin", "region_admin"])
    ).order_by(User.created_at.desc()).all()
    return [
        {"id": a.id, "nickname": a.nickname, "phone": a.phone,
         "role": a.role, "region_id": a.region_id, "status": a.status,
         "created_at": str(a.created_at)}
        for a in admins
    ]


@router.post("/admins")
def create_admin(
    phone: str = Query(...),
    password: str = Query(...),
    nickname: str = Query(default="管理员"),
    role: str = Query(default="region_admin"),
    region_id: int = Query(default=None),
    user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    if role not in ("region_admin", "super_admin"):
        raise HTTPException(status_code=400, detail="无效角色")
    existing = db.query(User).filter(User.phone == phone).first()
    if existing:
        raise HTTPException(status_code=400, detail="手机号已存在")
    admin = User(
        openid=f"admin_{phone}",
        nickname=nickname,
        phone=phone,
        role=role,
        region_id=region_id,
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
    admin = db.query(User).filter(User.id == user_id, User.role.in_(["super_admin", "region_admin"])).first()
    if not admin:
        raise HTTPException(status_code=404, detail="管理员不存在")
    admin.status = 0 if admin.status == 1 else 1
    db.commit()
    return {"message": f"已{'启用' if admin.status == 1 else '禁用'}"}


# ---- 区域管理 (增改) ----
@router.post("/regions")
def create_region(
    name: str = Query(...),
    parent_id: int = Query(default=None),
    user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    region = Region(name=name, parent_id=parent_id, sort_order=99, status=1)
    db.add(region)
    db.commit()
    db.refresh(region)
    return {"message": "区域已创建", "id": region.id}


@router.put("/regions/{region_id}")
def update_region(
    region_id: int,
    name: str = Query(default=None),
    parent_id: int = Query(default=None),
    sort_order: int = Query(default=None),
    status: int = Query(default=None),
    user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    region = db.query(Region).filter(Region.id == region_id).first()
    if not region:
        raise HTTPException(status_code=404, detail="区域不存在")
    if name is not None:
        region.name = name
    if parent_id is not None:
        region.parent_id = parent_id
    if sort_order is not None:
        region.sort_order = sort_order
    if status is not None:
        region.status = status
    db.commit()
    return {"message": "区域已更新"}


# ---- 订单统计 ----
@router.get("/orders/stats")
def order_stats(
    days: int = Query(default=7, le=90),
    user: User = Depends(require_any_admin),
    db: Session = Depends(get_db),
):
    """近 N 天每日订单数与营收"""
    from datetime import date, timedelta
    result = []
    for i in range(days - 1, -1, -1):
        d = date.today() - timedelta(days=i)
        region_filter = [Order.region_id == user.region_id] if user.role == "region_admin" and user.region_id else []
        count = db.query(func.count(Order.id)).filter(
            func.date(Order.created_at) == d,
            Order.status.in_(["completed", "delivered"]),
            *region_filter,
        ).scalar() or 0
        revenue = db.query(func.coalesce(func.sum(Order.total_price), 0)).filter(
            func.date(Order.created_at) == d,
            Order.status.in_(["completed", "delivered"]),
            *region_filter,
        ).scalar() or 0
        result.append({"date": str(d), "count": count, "revenue": round(float(revenue), 2)})
    return result
