# -*- coding: utf-8 -*-
"""订单模型 — 总单+子单架构"""
from sqlalchemy import Column, Integer, String, Enum as SQLEnum, DateTime, DECIMAL, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


# ============================================================
# 新架构：CombinedOrder（总单）+ SubOrder（子单）
# ============================================================

class CombinedOrder(Base):
    """总单 — 用户一次支付，跨多店合单，一份配送费"""
    __tablename__ = "combined_orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_no = Column(String(30), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    address_snapshot = Column(JSON, nullable=False)
    items_total = Column(DECIMAL(10, 2), nullable=False)
    delivery_fee_original = Column(DECIMAL(10, 2), default=0)
    delivery_fee_discount = Column(DECIMAL(10, 2), default=0)
    delivery_fee = Column(DECIMAL(10, 2), default=0)
    package_fee = Column(DECIMAL(10, 2), default=0)
    coupon_discount = Column(DECIMAL(10, 2), default=0)
    total_price = Column(DECIMAL(10, 2), nullable=False)
    status = Column(
        SQLEnum("pending_pay", "pending", "delivering", "completed", "partial", "cancelled"),
        nullable=False, default="pending_pay"
    )
    district_id = Column(Integer, ForeignKey("districts.id"), nullable=True)
    rider_id = Column(Integer, ForeignKey("riders.id"), nullable=True)
    user_coupon_id = Column(Integer, ForeignKey("user_coupons.id"), nullable=True)
    remark = Column(String(200), default="")
    paid_at = Column(DateTime, nullable=True)
    picked_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    sub_orders = relationship("SubOrder", back_populates="combined_order", lazy="joined")
    rider = relationship("Rider", lazy="joined")
    user = relationship("User", lazy="joined")


class SubOrder(Base):
    """子单 — 每个店铺独立流转"""
    __tablename__ = "sub_orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    combined_order_id = Column(Integer, ForeignKey("combined_orders.id", ondelete="CASCADE"), nullable=False)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    store_name_snapshot = Column(String(100), default="")
    items_total = Column(DECIMAL(10, 2), nullable=False)
    commission_rate = Column(DECIMAL(4, 3), default=0.120)
    status = Column(
        SQLEnum("pending_accept", "preparing", "ready", "delivering", "completed", "cancelled"),
        nullable=False, default="pending_accept"
    )
    cancel_reason = Column(String(300), default="")
    cancel_by = Column(String(20), default="")
    accepted_at = Column(DateTime, nullable=True)
    ready_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    combined_order = relationship("CombinedOrder", back_populates="sub_orders")
    store = relationship("Store", lazy="joined")
    items = relationship("SubOrderItem", back_populates="sub_order", lazy="joined")
    timeline = relationship("SubOrderTimeline", back_populates="sub_order", lazy="dynamic",
                            order_by="SubOrderTimeline.created_at")


class SubOrderItem(Base):
    """子单商品明细"""
    __tablename__ = "sub_order_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sub_order_id = Column(Integer, ForeignKey("sub_orders.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, nullable=True)
    name = Column(String(100), nullable=False)
    image = Column(String(500), default="")
    price = Column(DECIMAL(10, 2), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)

    sub_order = relationship("SubOrder", back_populates="items")


class SubOrderTimeline(Base):
    """子单时间线"""
    __tablename__ = "sub_order_timeline"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sub_order_id = Column(Integer, ForeignKey("sub_orders.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(30), nullable=False)
    description = Column(String(200), default="")
    created_at = Column(DateTime, server_default=func.now())

    sub_order = relationship("SubOrder", back_populates="timeline")


class OrderModification(Base):
    """订单修改申请 — 用户申请退单/改地址等，商家/管理员审核"""
    __tablename__ = "order_modifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    combined_order_id = Column(Integer, ForeignKey("combined_orders.id", ondelete="CASCADE"), nullable=False)
    sub_order_id = Column(Integer, ForeignKey("sub_orders.id", ondelete="CASCADE"), nullable=True)
    type = Column(String(30), nullable=False, default="cancel")  # cancel / address_change / refund / other
    reason = Column(String(500), default="")
    new_address = Column(JSON, nullable=True)  # type=address_change 时新的地址信息
    status = Column(String(20), nullable=False, default="pending_review")  # pending_review / approved / rejected
    reviewed_by = Column(Integer, nullable=True)  # 审核人user_id
    review_comment = Column(String(300), default="")
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class OrderReview(Base):
    """子单评价"""
    __tablename__ = "order_reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sub_order_id = Column(Integer, ForeignKey("sub_orders.id", ondelete="CASCADE"), nullable=False, unique=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    score = Column(Integer, nullable=False)
    content = Column(String(500), default="")
    tags = Column(JSON, default=[])
    created_at = Column(DateTime, server_default=func.now())


class OrderMessage(Base):
    """订单留言 — 骑手与用户之间的沟通"""
    __tablename__ = "order_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    combined_order_id = Column(Integer, ForeignKey("combined_orders.id", ondelete="CASCADE"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    sender_role = Column(String(10), nullable=False, default="user")  # user / rider
    content = Column(String(500), default="")
    created_at = Column(DateTime, server_default=func.now())

    combined_order = relationship("CombinedOrder", lazy="joined")


# ============================================================
# 旧模型 — 保留兼容，标记 deprecated
# ============================================================

class Order(Base):
    """[deprecated] 旧订单模型 — 将被 CombinedOrder + SubOrder 替代"""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_no = Column(String(30), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    rider_id = Column(Integer, ForeignKey("riders.id"), nullable=True)
    address_snapshot = Column(JSON, nullable=False)
    items_total = Column(DECIMAL(10, 2), nullable=False)
    delivery_fee = Column(DECIMAL(10, 2), default=0)
    package_fee = Column(DECIMAL(10, 2), default=0)
    discount_amount = Column(DECIMAL(10, 2), default=0)
    total_price = Column(DECIMAL(10, 2), nullable=False)
    status = Column(
        SQLEnum("pending_pay", "pending_accept", "preparing", "ready",
                "delivering", "delivered", "completed", "cancelled"),
        nullable=False, default="pending_pay"
    )
    cancel_reason = Column(String(300), default="")
    cancel_by = Column(String(20), default="")
    remark = Column(String(200), default="")
    paid_at = Column(DateTime, nullable=True)
    accepted_at = Column(DateTime, nullable=True)
    ready_at = Column(DateTime, nullable=True)
    picked_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    district_id = Column(Integer, ForeignKey("districts.id"), nullable=True)
    user_coupon_id = Column(Integer, ForeignKey("user_coupons.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    items = relationship("OrderItem", back_populates="order", lazy="joined")
    timeline = relationship("OrderTimeline", back_populates="order", lazy="dynamic",
                            order_by="OrderTimeline.created_at")
    user = relationship("User", lazy="joined")
    store = relationship("Store", back_populates="orders", lazy="joined")
    rider = relationship("Rider", lazy="joined")


class OrderItem(Base):
    """[deprecated] 旧订单商品明细"""
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, nullable=True)
    name = Column(String(100), nullable=False)
    image = Column(String(500), default="")
    price = Column(DECIMAL(10, 2), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)

    order = relationship("Order", back_populates="items")


class OrderTimeline(Base):
    """[deprecated] 旧订单时间线"""
    __tablename__ = "order_timeline"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(30), nullable=False)
    description = Column(String(200), default="")
    created_at = Column(DateTime, server_default=func.now())

    order = relationship("Order", back_populates="timeline")
