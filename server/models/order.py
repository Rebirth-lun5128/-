from sqlalchemy import Column, Integer, String, Enum as SQLEnum, DateTime, DECIMAL, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_no = Column(String(30), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)
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
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    items = relationship("OrderItem", back_populates="order", lazy="joined")
    timeline = relationship("OrderTimeline", back_populates="order", lazy="dynamic",
                            order_by="OrderTimeline.created_at")
    user = relationship("User", lazy="joined")
    restaurant = relationship("Restaurant", lazy="joined")
    rider = relationship("Rider", lazy="joined")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    menu_item_id = Column(Integer, nullable=True)
    name = Column(String(100), nullable=False)
    image = Column(String(500), default="")
    price = Column(DECIMAL(10, 2), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)

    order = relationship("Order", back_populates="items")


class OrderTimeline(Base):
    __tablename__ = "order_timeline"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(30), nullable=False)
    description = Column(String(200), default="")
    created_at = Column(DateTime, server_default=func.now())

    order = relationship("Order", back_populates="timeline")
