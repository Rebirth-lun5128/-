from sqlalchemy import Column, Integer, String, Text, Enum as SQLEnum, DateTime, DECIMAL
from sqlalchemy.sql import func

from database import Base


class Settlement(Base):
    __tablename__ = "settlements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    target_type = Column(SQLEnum("store", "rider"), nullable=False)
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
    config_value = Column(Text, nullable=False)
    description = Column(String(200), default="")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
