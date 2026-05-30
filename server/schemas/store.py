from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


# ---- District ----
class DistrictUpdate(BaseModel):
    name: Optional[str] = None
    coverage: Optional[str] = None       # JSON string
    delivery_fee: Optional[int] = None
    delivery_range: Optional[int] = None
    notice: Optional[str] = None
    admin_id: Optional[int] = None
    status: Optional[int] = None


# ---- Product ----
class ProductOut(BaseModel):
    id: int
    store_id: int
    category_id: Optional[int]
    name: str
    image: str
    price: float
    original_price: Optional[float]
    description: str
    stock: int
    limit_per_order: int
    monthly_sales: int
    is_recommended: int
    status: int
    sort_order: int

    model_config = ConfigDict(from_attributes=True)


class ProductCreate(BaseModel):
    category_id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=100)
    image: str = ""
    price: float = Field(..., gt=0)
    original_price: Optional[float] = None
    description: str = ""
    stock: int = -1
    limit_per_order: int = 0
    is_recommended: int = 0
    sort_order: int = 0


class ProductUpdate(BaseModel):
    category_id: Optional[int] = None
    name: Optional[str] = None
    image: Optional[str] = None
    price: Optional[float] = None
    original_price: Optional[float] = None
    description: Optional[str] = None
    stock: Optional[int] = None
    limit_per_order: Optional[int] = None
    is_recommended: Optional[int] = None
    status: Optional[int] = None
    sort_order: Optional[int] = None


# ---- Store Category ----
class StoreCategoryOut(BaseModel):
    id: int
    store_id: int
    name: str
    sort_order: int
    products: List[ProductOut] = []

    model_config = ConfigDict(from_attributes=True)


class StoreCategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    sort_order: int = 0


# ---- Store ----
class StoreOut(BaseModel):
    id: int
    user_id: int
    district_id: Optional[int]
    store_type: str
    name: str
    logo: str
    banner: str
    phone: str
    address: str
    lat: Optional[float]
    lng: Optional[float]
    category: str
    rating: float
    monthly_sales: int
    min_price: float
    delivery_fee: float
    effective_delivery_fee: float = 0  # 实际配送费（从分区读取，元）
    delivery_time: str
    business_hours: Optional[dict]
    notice: str
    status: str
    verify_status: str
    stall_location: str
    stall_photo: str
    id_card_photo: str
    combinable_districts: Optional[List[int]] = None
    district_name: str = ""
    qr_code: str = ""

    model_config = ConfigDict(from_attributes=True)


class StoreDetailOut(StoreOut):
    categories: List[StoreCategoryOut] = []


class StoreUpdate(BaseModel):
    name: Optional[str] = None
    store_type: Optional[str] = None
    logo: Optional[str] = None
    banner: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    category: Optional[str] = None
    min_price: Optional[float] = None
    delivery_fee: Optional[float] = None
    district_id: Optional[int] = None
    combinable_districts: Optional[List[int]] = None
    delivery_time: Optional[str] = None
    business_hours: Optional[dict] = None
    notice: Optional[str] = None
    status: Optional[str] = None
    stall_location: Optional[str] = None
    id_card_photo: Optional[str] = None
    stall_photo: Optional[str] = None


class StoreListOut(BaseModel):
    total: int
    items: List[StoreOut]
