from datetime import date, datetime

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from auth import require_merchant
from database import get_db
from models.user import User
from models.store import Store
from models.order import SubOrder, OrderModification
from models.region import SystemConfig, Settlement
from sqlalchemy import func
from schemas.store import StoreOut, StoreUpdate

router = APIRouter(prefix="/api/merchant/shop", tags=["商家端-店铺"])


def _get_merchant_store(user: User, db: Session) -> Store:
    store = db.query(Store).filter(Store.user_id == user.id).first()
    if not store:
        raise HTTPException(status_code=404, detail="请先完成店铺入驻")
    return store


@router.get("", response_model=StoreOut)
def get_shop(user: User = Depends(require_merchant), db: Session = Depends(get_db)):
    return _get_merchant_store(user, db)


@router.put("", response_model=StoreOut)
def update_shop(
    body: StoreUpdate,
    user: User = Depends(require_merchant),
    db: Session = Depends(get_db),
):
    store = _get_merchant_store(user, db)
    update_data = body.model_dump(exclude_unset=True)
    for key, val in update_data.items():
        setattr(store, key, val)
    db.commit()
    db.refresh(store)
    return store


@router.put("/toggle-status")
def toggle_status(user: User = Depends(require_merchant), db: Session = Depends(get_db)):
    """快捷切换营业状态: 出摊 → 休息 → 收摊 → 出摊"""
    store = _get_merchant_store(user, db)
    cycle = {"open": "resting", "resting": "closed", "closed": "open"}
    store.status = cycle.get(store.status, "closed")
    status_labels = {"open": "已出摊", "resting": "已休息", "closed": "已收摊"}
    db.commit()
    return {"status": store.status, "message": status_labels.get(store.status, store.status)}


@router.post("/register", response_model=StoreOut)
def register_shop(
    body: StoreUpdate,
    user: User = Depends(require_merchant),
    db: Session = Depends(get_db),
):
    """商家入驻 — 无需营业执照，提交基本信息即可"""
    existing = db.query(Store).filter(Store.user_id == user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="已入驻，请勿重复操作")

    store = Store(
        user_id=user.id,
        name=body.name or f"{user.nickname}的摊位",
        phone=body.phone or user.phone,
        address=body.address or "",
        stall_location=body.stall_location or body.address or "",
        id_card_photo=body.id_card_photo or "",
        stall_photo=body.stall_photo or "",
        category=body.category or "夜市小吃",
        store_type=body.store_type or "stall",
        status="closed",
        verify_status="unverified",
    )
    db.add(store)
    db.commit()
    db.refresh(store)
    return store


@router.get("/dashboard")
def dashboard(user: User = Depends(require_merchant), db: Session = Depends(get_db)):
    store = _get_merchant_store(user, db)

    today_orders = db.query(SubOrder).filter(
        SubOrder.store_id == store.id,
        func.date(SubOrder.created_at) == date.today(),
    )
    today_count = today_orders.count()
    today_revenue = db.query(func.coalesce(func.sum(SubOrder.items_total), 0)).filter(
        SubOrder.store_id == store.id,
        func.date(SubOrder.created_at) == date.today(),
        SubOrder.status.in_(["completed", "delivering"]),
    ).scalar() or 0

    pending_count = db.query(SubOrder).filter(
        SubOrder.store_id == store.id,
        SubOrder.status.in_(["pending_accept", "preparing", "ready"]),
    ).count()

    # 待审核的修改申请
    sub_ids = db.query(SubOrder.id).filter(SubOrder.store_id == store.id).all()
    sub_id_list = [s[0] for s in sub_ids]
    pending_modifications = 0
    if sub_id_list:
        pending_modifications = db.query(OrderModification).filter(
            OrderModification.sub_order_id.in_(sub_id_list),
            OrderModification.status == "pending_review",
        ).count()

    return {
        "today_orders": today_count,
        "today_revenue": float(today_revenue),
        "pending_orders": pending_count,
        "pending_modifications": pending_modifications,
        "monthly_sales": store.monthly_sales,
        "rating": float(store.rating),
        "status": store.status,
        "verify_status": store.verify_status,
        "commission_rate": float(store.commission_rate or 0.12),
    }


@router.get("/settlement")
def settlement(user: User = Depends(require_merchant), db: Session = Depends(get_db)):
    """商家结算数据"""
    store = _get_merchant_store(user, db)

    total_revenue = db.query(func.coalesce(func.sum(SubOrder.items_total), 0)).filter(
        SubOrder.store_id == store.id,
        SubOrder.status.in_(["completed", "delivering"]),
    ).scalar() or 0

    total_orders = db.query(func.count(SubOrder.id)).filter(
        SubOrder.store_id == store.id,
        SubOrder.status.in_(["completed", "delivering"]),
    ).scalar() or 0

    fee_rate = float(store.commission_rate or 0.12)

    platform_fee = float(total_revenue) * fee_rate
    net_revenue = float(total_revenue) - platform_fee

    settled_amount = db.query(func.coalesce(func.sum(Settlement.net_amount), 0)).filter(
        Settlement.target_type == "store",
        Settlement.target_id == store.id,
        Settlement.status == "paid",
    ).scalar() or 0

    pending_settlement = max(0, net_revenue - float(settled_amount))

    records = db.query(Settlement).filter(
        Settlement.target_type == "store",
        Settlement.target_id == store.id,
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
                "id": r.id, "amount": float(r.amount), "fee": float(r.fee),
                "net_amount": float(r.net_amount), "period": r.period,
                "status": r.status, "paid_at": str(r.paid_at) if r.paid_at else None,
                "created_at": str(r.created_at),
            }
            for r in records
        ],
    }


@router.post("/withdraw")
def withdraw(
    amount: float = Body(..., gt=0, embed=True),
    user: User = Depends(require_merchant),
    db: Session = Depends(get_db),
):
    """商家申请结算（管理员审核后线下打款）"""
    store = _get_merchant_store(user, db)

    total_revenue = db.query(func.coalesce(func.sum(SubOrder.items_total), 0)).filter(
        SubOrder.store_id == store.id,
        SubOrder.status.in_(["completed", "delivering"]),
    ).scalar() or 0

    fee_rate = float(store.commission_rate or 0.12)
    platform_fee = float(total_revenue) * fee_rate
    net_revenue = float(total_revenue) - platform_fee

    settled_amount = db.query(func.coalesce(func.sum(Settlement.net_amount), 0)).filter(
        Settlement.target_type == "store",
        Settlement.target_id == store.id,
        Settlement.status == "paid",
    ).scalar() or 0

    pending_settlement = db.query(func.coalesce(func.sum(Settlement.net_amount), 0)).filter(
        Settlement.target_type == "store",
        Settlement.target_id == store.id,
        Settlement.status == "pending",
    ).scalar() or 0

    available = max(0, net_revenue - float(settled_amount) - float(pending_settlement))
    if amount > available:
        raise HTTPException(status_code=400, detail=f"可结算金额不足，当前可结算 ¥{available:.2f}")
    if amount < 1:
        raise HTTPException(status_code=400, detail="结算金额不能少于1元")

    period = datetime.now().strftime("%Y-%m")
    db.add(Settlement(
        target_type="store", target_id=store.id,
        amount=amount, fee=0, net_amount=amount,
        period=period, status="pending",
    ))
    db.commit()
    return {
        "message": f"已提交 ¥{amount:.2f} 结算申请，等待管理员处理",
        "settlement_amount": amount,
        "remain": round(available - amount, 2),
    }
