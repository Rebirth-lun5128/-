"""用户端优惠券"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import require_user
from database import get_db
from models.user import User
from models.coupon import Coupon, UserCoupon

router = APIRouter(prefix="/api/user/coupons", tags=["用户端-优惠券"])


@router.get("/available")
def list_available(user: User = Depends(require_user), db: Session = Depends(get_db)):
    """可领取的优惠券"""
    coupons = db.query(Coupon).filter(
        Coupon.status == 1,
    ).all()
    # 过滤已领完的
    result = []
    for c in coupons:
        if c.total_count > 0 and c.used_count >= c.total_count:
            continue
        # 检查是否已领取
        already = db.query(UserCoupon).filter(
            UserCoupon.user_id == user.id,
            UserCoupon.coupon_id == c.id,
        ).first()
        result.append({
            "id": c.id, "name": c.name, "coupon_type": c.coupon_type,
            "condition_amount": float(c.condition_amount),
            "discount_amount": float(c.discount_amount),
            "start_time": str(c.start_time) if c.start_time else None,
            "end_time": str(c.end_time) if c.end_time else None,
            "claimed": already is not None,
        })
    return result


@router.post("/{coupon_id}/claim")
def claim_coupon(coupon_id: int, user: User = Depends(require_user), db: Session = Depends(get_db)):
    """领取优惠券"""
    coupon = db.query(Coupon).filter(Coupon.id == coupon_id, Coupon.status == 1).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="优惠券不存在")
    if coupon.total_count > 0 and coupon.used_count >= coupon.total_count:
        raise HTTPException(status_code=400, detail="已领完")

    existing = db.query(UserCoupon).filter(
        UserCoupon.user_id == user.id,
        UserCoupon.coupon_id == coupon_id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="已领取过")

    uc = UserCoupon(user_id=user.id, coupon_id=coupon_id)
    coupon.used_count += 1
    db.add(uc)
    db.commit()
    return {"message": "领取成功", "id": uc.id}


@router.get("/my")
def my_coupons(user: User = Depends(require_user), db: Session = Depends(get_db)):
    """我的优惠券"""
    ucs = db.query(UserCoupon).filter(
        UserCoupon.user_id == user.id,
    ).join(Coupon).order_by(UserCoupon.created_at.desc()).all()
    result = []
    for uc in ucs:
        c = db.query(Coupon).filter(Coupon.id == uc.coupon_id).first()
        if c:
            result.append({
                "id": uc.id, "coupon_id": c.id, "name": c.name,
                "coupon_type": c.coupon_type,
                "condition_amount": float(c.condition_amount),
                "discount_amount": float(c.discount_amount),
                "status": uc.status,
                "created_at": str(uc.created_at),
                "used_at": str(uc.used_at) if uc.used_at else None,
            })
    return result
