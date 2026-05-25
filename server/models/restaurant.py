from sqlalchemy import Column, Integer, String, Enum as SQLEnum, DateTime, DECIMAL, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class Restaurant(Base):
    __tablename__ = "restaurants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    logo = Column(String(500), default="")
    banner = Column(String(500), default="")
    phone = Column(String(20), default="")
    address = Column(String(300), default="")
    lat = Column(DECIMAL(10, 7), nullable=True)
    lng = Column(DECIMAL(10, 7), nullable=True)
    category = Column(String(50), default="")
    rating = Column(DECIMAL(2, 1), default=5.0)
    monthly_sales = Column(Integer, default=0)
    min_price = Column(DECIMAL(10, 2), default=0)
    delivery_fee = Column(DECIMAL(10, 2), default=0)
    delivery_time = Column(String(20), default="30分钟")
    business_hours = Column(JSON, nullable=True)
    notice = Column(String(200), default="")
    status = Column(SQLEnum("open", "closed", "resting"), default="closed")
    verify_status = Column(SQLEnum("unverified", "verified", "rejected"), default="unverified")
    verify_method = Column(String(50), default="")  # 核验方式: 现场核验/视频核验/证件核验
    verify_note = Column(String(300), default="")   # 核验备注
    stall_location = Column(String(300), default="") # 夜市摊位位置描述
    id_card_photo = Column(String(500), default="")  # 身份证照片(可选)
    stall_photo = Column(String(500), default="")     # 摊位照片(可选)
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    owner = relationship("User", back_populates="restaurant")
    categories = relationship("MenuCategory", back_populates="restaurant", lazy="dynamic",
                              order_by="MenuCategory.sort_order")
    items = relationship("MenuItem", back_populates="restaurant", lazy="dynamic")


class MenuCategory(Base):
    __tablename__ = "menu_categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(50), nullable=False)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())

    restaurant = relationship("Restaurant", back_populates="categories")
    items = relationship("MenuItem", back_populates="category", lazy="dynamic",
                         order_by="MenuItem.sort_order")


class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("menu_categories.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(100), nullable=False)
    image = Column(String(500), default="")
    price = Column(DECIMAL(10, 2), nullable=False)
    original_price = Column(DECIMAL(10, 2), nullable=True)
    description = Column(String(300), default="")
    monthly_sales = Column(Integer, default=0)
    is_recommended = Column(Integer, default=0)
    status = Column(Integer, default=1)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    restaurant = relationship("Restaurant", back_populates="items")
    category = relationship("MenuCategory", back_populates="items")
