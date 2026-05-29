"""店铺 & 商品模型 — 统一抽象夜市摊位、家庭厨房、自营商品"""
from sqlalchemy import Column, Integer, String, Enum as SQLEnum, DateTime, DECIMAL, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base
from models.district import District


class Store(Base):
    __tablename__ = "stores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    district_id = Column(Integer, ForeignKey("districts.id"), nullable=True)
    # 店铺类型: 夜市摊位 / 家庭厨房 / 平台自营
    store_type = Column(SQLEnum("stall", "home_kitchen", "self_operated"), nullable=False, default="stall")
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
    delivery_fee = Column(DECIMAL(10, 2), default=0)           # [deprecated] 配送费改由 District 管理
    delivery_surcharge = Column(DECIMAL(10, 2), default=0)     # 配送附加费(元)，管理端设置
    commission_rate = Column(DECIMAL(4, 3), default=0.120)     # 抽成比例 0~1，默认12%
    combinable_districts = Column(JSON, nullable=True)           # 可合单的分区 ID 列表, null/[]=仅本区
    delivery_time = Column(String(20), default="30分钟")
    business_hours = Column(JSON, nullable=True)
    notice = Column(String(200), default="")
    status = Column(SQLEnum("open", "closed", "resting"), default="closed")    # 出摊/收摊/休息
    verify_status = Column(SQLEnum("unverified", "verified", "rejected"), default="unverified")
    verify_method = Column(String(50), default="")
    verify_note = Column(String(300), default="")
    stall_location = Column(String(300), default="")
    id_card_photo = Column(String(500), default="")
    stall_photo = Column(String(500), default="")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    owner = relationship("User", back_populates="store")
    district = relationship(District, lazy="joined")
    categories = relationship("StoreCategory", back_populates="store", lazy="dynamic",
                              order_by="StoreCategory.sort_order")
    products = relationship("Product", back_populates="store", lazy="dynamic")
    orders = relationship("Order", back_populates="store")

    @property
    def district_name(self):
        return self.district.name if self.district else ""


class StoreCategory(Base):
    __tablename__ = "store_categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    store_id = Column(Integer, ForeignKey("stores.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(50), nullable=False)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())

    store = relationship("Store", back_populates="categories")
    products = relationship("Product", back_populates="category", lazy="dynamic",
                            order_by="Product.sort_order")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    store_id = Column(Integer, ForeignKey("stores.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("store_categories.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(100), nullable=False)
    image = Column(String(500), default="")
    price = Column(DECIMAL(10, 2), nullable=False)
    original_price = Column(DECIMAL(10, 2), nullable=True)
    description = Column(String(300), default="")
    stock = Column(Integer, default=-1)              # 库存, -1=不限
    limit_per_order = Column(Integer, default=0)     # 每单限购, 0=不限
    monthly_sales = Column(Integer, default=0)
    is_recommended = Column(Integer, default=0)
    status = Column(Integer, default=1)              # 1=上架 0=下架
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    store = relationship("Store", back_populates="products")
    category = relationship("StoreCategory", back_populates="products")
