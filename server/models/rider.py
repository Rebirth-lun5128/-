from sqlalchemy import Column, Integer, String, Enum as SQLEnum, DateTime, DECIMAL, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class Rider(Base):
    __tablename__ = "riders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    real_name = Column(String(50), nullable=False)
    id_card = Column(String(20), default="")
    phone = Column(String(20), nullable=False)
    status = Column(SQLEnum("offline", "online", "busy"), default="offline")
    lat = Column(DECIMAL(10, 7), nullable=True)
    lng = Column(DECIMAL(10, 7), nullable=True)
    balance = Column(DECIMAL(10, 2), default=0)
    total_orders = Column(Integer, default=0)
    rating = Column(DECIMAL(2, 1), default=5.0)
    audit_status = Column(SQLEnum("pending", "approved", "rejected"), default="pending")
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="rider_info")
