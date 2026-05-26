from sqlalchemy import Column, Integer, String, Enum as SQLEnum, DateTime, DECIMAL, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    openid = Column(String(100), unique=True, default="")
    unionid = Column(String(100), default="")
    nickname = Column(String(100), default="")
    avatar = Column(String(500), default="")
    phone = Column(String(20), default="")
    hashed_password = Column(String(200), default="")
    role = Column(SQLEnum("user", "merchant", "rider", "district_admin", "super_admin"), nullable=False, default="user")
    district_id = Column(Integer, ForeignKey("districts.id"), nullable=True)
    status = Column(Integer, default=1)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    addresses = relationship("UserAddress", back_populates="user", lazy="dynamic")
    store = relationship("Store", back_populates="owner", uselist=False)
    rider_info = relationship("Rider", back_populates="user", uselist=False)


class UserAddress(Base):
    __tablename__ = "user_addresses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    contact_name = Column(String(50), nullable=False)
    contact_phone = Column(String(20), nullable=False)
    gender = Column(Integer, default=1)
    province = Column(String(50), default="")
    city = Column(String(50), default="")
    district = Column(String(50), default="")
    detail = Column(String(200), nullable=False)
    lat = Column(DECIMAL(10, 7), nullable=True)
    lng = Column(DECIMAL(10, 7), nullable=True)
    label = Column(String(50), default="")
    is_default = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="addresses")
