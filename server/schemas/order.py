from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


# ---- Order Item ----
class OrderItemIn(BaseModel):
    menu_item_id: int
    name: str
    image: str = ""
    price: float
    quantity: int = Field(default=1, ge=1)


class OrderItemOut(BaseModel):
    id: int
    name: str
    image: str
    price: float
    quantity: int

    model_config = ConfigDict(from_attributes=True)


# ---- Order ----
class OrderCreate(BaseModel):
    restaurant_id: int
    address_id: int
    items: List[OrderItemIn] = Field(..., min_length=1)
    remark: str = ""


class OrderOut(BaseModel):
    id: int
    order_no: str
    user_id: int
    restaurant_id: int
    rider_id: Optional[int]
    address_snapshot: dict
    items_total: float
    delivery_fee: float
    package_fee: float
    discount_amount: float
    total_price: float
    status: str
    cancel_reason: str
    cancel_by: str
    remark: str
    paid_at: Optional[datetime]
    accepted_at: Optional[datetime]
    ready_at: Optional[datetime]
    picked_at: Optional[datetime]
    delivered_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    items: List[OrderItemOut] = []
    restaurant_name: str = ""
    rider_name: str = ""

    model_config = ConfigDict(from_attributes=True)


class OrderListOut(BaseModel):
    total: int
    items: List[OrderOut]


# ---- Order Timeline ----
class TimelineOut(BaseModel):
    id: int
    status: str
    description: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderDetailOut(OrderOut):
    timeline: List[TimelineOut] = []
