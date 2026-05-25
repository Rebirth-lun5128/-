from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


# ---- Menu Item ----
class MenuItemOut(BaseModel):
    id: int
    restaurant_id: int
    category_id: Optional[int]
    name: str
    image: str
    price: float
    original_price: Optional[float]
    description: str
    monthly_sales: int
    is_recommended: int
    status: int
    sort_order: int

    model_config = ConfigDict(from_attributes=True)


class MenuItemCreate(BaseModel):
    category_id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=100)
    image: str = ""
    price: float = Field(..., gt=0)
    original_price: Optional[float] = None
    description: str = ""
    is_recommended: int = 0
    sort_order: int = 0


class MenuItemUpdate(BaseModel):
    category_id: Optional[int] = None
    name: Optional[str] = None
    image: Optional[str] = None
    price: Optional[float] = None
    original_price: Optional[float] = None
    description: Optional[str] = None
    is_recommended: Optional[int] = None
    status: Optional[int] = None
    sort_order: Optional[int] = None


# ---- Menu Category ----
class MenuCategoryOut(BaseModel):
    id: int
    restaurant_id: int
    name: str
    sort_order: int
    items: List[MenuItemOut] = []

    model_config = ConfigDict(from_attributes=True)


class MenuCategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    sort_order: int = 0


# ---- Restaurant ----
class RestaurantOut(BaseModel):
    id: int
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
    delivery_time: str
    business_hours: Optional[dict]
    notice: str
    status: str
    verify_status: str

    model_config = ConfigDict(from_attributes=True)


class RestaurantDetailOut(RestaurantOut):
    categories: List[MenuCategoryOut] = []


class RestaurantUpdate(BaseModel):
    name: Optional[str] = None
    logo: Optional[str] = None
    banner: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    category: Optional[str] = None
    min_price: Optional[float] = None
    delivery_fee: Optional[float] = None
    delivery_time: Optional[str] = None
    business_hours: Optional[dict] = None
    notice: Optional[str] = None
    status: Optional[str] = None
    stall_location: Optional[str] = None
    id_card_photo: Optional[str] = None
    stall_photo: Optional[str] = None


class RestaurantListOut(BaseModel):
    total: int
    items: List[RestaurantOut]
