from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import require_merchant
from database import get_db
from models.user import User
from models.restaurant import Restaurant
from schemas.restaurant import RestaurantOut, RestaurantUpdate

router = APIRouter(prefix="/api/merchant/shop", tags=["商家端-店铺"])


def _get_merchant_restaurant(user: User, db: Session) -> Restaurant:
    restaurant = db.query(Restaurant).filter(Restaurant.user_id == user.id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="请先完成店铺入驻")
    return restaurant


@router.get("", response_model=RestaurantOut)
def get_shop(user: User = Depends(require_merchant), db: Session = Depends(get_db)):
    return _get_merchant_restaurant(user, db)


@router.put("", response_model=RestaurantOut)
def update_shop(
    body: RestaurantUpdate,
    user: User = Depends(require_merchant),
    db: Session = Depends(get_db),
):
    restaurant = _get_merchant_restaurant(user, db)
    update_data = body.model_dump(exclude_unset=True)
    for key, val in update_data.items():
        setattr(restaurant, key, val)
    db.commit()
    db.refresh(restaurant)
    return restaurant


@router.post("/register", response_model=RestaurantOut)
def register_shop(
    body: RestaurantUpdate,
    user: User = Depends(require_merchant),
    db: Session = Depends(get_db),
):
    """
    商家入驻 — 无需营业执照，提交基本信息即可
    平台后续通过 verify_status 进行人工核验（现场核验/视频核验）
    """
    existing = db.query(Restaurant).filter(Restaurant.user_id == user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="已入驻，请勿重复操作")

    restaurant = Restaurant(
        user_id=user.id,
        name=body.name or f"{user.nickname}的摊位",
        phone=body.phone or user.phone,
        address=body.address or "",
        stall_location=body.stall_location or body.address or "",
        id_card_photo=body.id_card_photo or "",
        stall_photo=body.stall_photo or "",
        category=body.category or "夜市小吃",
        status="closed",
        verify_status="unverified",  # 等待平台核验
    )
    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)
    return restaurant


@router.get("/dashboard")
def dashboard(user: User = Depends(require_merchant), db: Session = Depends(get_db)):
    from models.order import Order
    from sqlalchemy import func
    restaurant = _get_merchant_restaurant(user, db)

    # 今日数据
    today_orders = db.query(Order).filter(
        Order.restaurant_id == restaurant.id,
        func.date(Order.created_at) == date.today(),
    )
    today_count = today_orders.count()
    today_revenue = db.query(func.coalesce(func.sum(Order.total_price), 0)).filter(
        Order.restaurant_id == restaurant.id,
        func.date(Order.created_at) == date.today(),
        Order.status.in_(["completed", "delivered"]),
    ).scalar() or 0

    # 待处理订单
    pending_count = db.query(Order).filter(
        Order.restaurant_id == restaurant.id,
        Order.status.in_(["pending_accept", "preparing", "ready"]),
    ).count()

    return {
        "today_orders": today_count,
        "today_revenue": float(today_revenue),
        "pending_orders": pending_count,
        "monthly_sales": restaurant.monthly_sales,
        "rating": float(restaurant.rating),
        "status": restaurant.status,
        "verify_status": restaurant.verify_status,  # 核验状态
    }


@router.get("/settlement")
def settlement(user: User = Depends(require_merchant), db: Session = Depends(get_db)):
    """商家结算数据 — 累计收入 & 结算记录"""
    from models.order import Order
    from models.region import Settlement
    from sqlalchemy import func

    restaurant = _get_merchant_restaurant(user, db)

    # 累计已完成订单金额
    total_revenue = db.query(func.coalesce(func.sum(Order.total_price), 0)).filter(
        Order.restaurant_id == restaurant.id,
        Order.status.in_(["completed", "delivered"]),
    ).scalar() or 0

    total_orders = db.query(func.count(Order.id)).filter(
        Order.restaurant_id == restaurant.id,
        Order.status.in_(["completed", "delivered"]),
    ).scalar() or 0

    # 平台抽成比例
    from models.region import SystemConfig
    config = db.query(SystemConfig).filter(SystemConfig.config_key == "platform_fee_rate").first()
    fee_rate = float(config.config_value) if config else 0.15

    platform_fee = float(total_revenue) * fee_rate
    net_revenue = float(total_revenue) - platform_fee

    # 已结算金额
    settled_amount = db.query(func.coalesce(func.sum(Settlement.net_amount), 0)).filter(
        Settlement.target_type == "restaurant",
        Settlement.target_id == restaurant.id,
        Settlement.status == "paid",
    ).scalar() or 0

    # 待结算 = 净收入 - 已结算
    pending_settlement = max(0, net_revenue - float(settled_amount))

    # 结算记录
    records = db.query(Settlement).filter(
        Settlement.target_type == "restaurant",
        Settlement.target_id == restaurant.id,
    ).order_by(Settlement.created_at.desc()).all()

    return {
        "total_revenue": round(float(total_revenue), 2),
        "total_orders": total_orders,
        "fee_rate": fee_rate,
        "platform_fee": round(platform_fee, 2),
        "net_revenue": round(net_revenue, 2),
        "settled_amount": round(float(settled_amount), 2),
        "pending_settlement": round(pending_settlement, 2),
        "records": [
            {
                "id": r.id,
                "amount": float(r.amount),
                "fee": float(r.fee),
                "net_amount": float(r.net_amount),
                "period": r.period,
                "status": r.status,
                "paid_at": str(r.paid_at) if r.paid_at else None,
                "created_at": str(r.created_at),
            }
            for r in records
        ],
    }
