"""营销模型 — 优惠券"""
from sqlalchemy import Column, Integer, String, Enum as SQLEnum, DateTime, DECIMAL, ForeignKey
from sqlalchemy.sql import func

from database import Base


class Coupon(Base):
    __tablename__ = "coupons"

    id = Column(Integer, primary_key=True, autoincrement=True)
    district_id = Column(Integer, ForeignKey("districts.id"), nullable=True)   # 分区范围, NULL=全平台
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=True)         # 指定店铺, NULL=通用
    name = Column(String(100), nullable=False)
    coupon_type = Column(SQLEnum("new_user", "full_reduction", "direct_discount"), nullable=False)
    condition_amount = Column(DECIMAL(10, 2), default=0)     # 满减门槛(元)
    discount_amount = Column(DECIMAL(10, 2), nullable=False)  # 减免金额(元)
    total_count = Column(Integer, default=0)                  # 发放总量, 0=不限
    used_count = Column(Integer, default=0)                   # 已领取数
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    status = Column(Integer, default=1)                       # 1=启用 0=停用
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class UserCoupon(Base):
    __tablename__ = "user_coupons"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    coupon_id = Column(Integer, ForeignKey("coupons.id"), nullable=False)
    status = Column(SQLEnum("unused", "used", "expired"), default="unused")
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
