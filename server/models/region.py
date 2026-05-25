from sqlalchemy import Column, Integer, String, Enum as SQLEnum, DateTime, DECIMAL, ForeignKey, JSON
from sqlalchemy.sql import func

from database import Base


class Region(Base):
    __tablename__ = "regions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    parent_id = Column(Integer, ForeignKey("regions.id", ondelete="SET NULL"), nullable=True)
    manager_id = Column(Integer, nullable=True)
    sort_order = Column(Integer, default=0)
    status = Column(Integer, default=1)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Settlement(Base):
    __tablename__ = "settlements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    target_type = Column(SQLEnum("restaurant", "rider"), nullable=False)
    target_id = Column(Integer, nullable=False)
    amount = Column(DECIMAL(10, 2), nullable=False)
    fee = Column(DECIMAL(10, 2), default=0)
    net_amount = Column(DECIMAL(10, 2), nullable=False)
    period = Column(String(20), default="")
    status = Column(SQLEnum("pending", "paid"), default="pending")
    paid_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class SystemConfig(Base):
    __tablename__ = "system_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    config_key = Column(String(50), unique=True, nullable=False)
    config_value = Column(String(500), nullable=False)
    description = Column(String(200), default="")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
