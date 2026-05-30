from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


# ---- 商品项 ----
class OrderItemIn(BaseModel):
    product_id: int
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


# ============================================================
# 新架构：CombinedOrder + SubOrder
# ============================================================

class SubOrderItemCreate(BaseModel):
    store_id: int
    items: List[OrderItemIn] = Field(..., min_length=1)


class CombinedOrderCreate(BaseModel):
    address_id: int
    sub_orders: List[SubOrderItemCreate] = Field(..., min_length=1)
    remark: str = ""
    user_coupon_id: Optional[int] = None


# ---- 子单输出 ----
class SubOrderItemOut(BaseModel):
    id: int
    product_id: Optional[int]
    name: str
    image: str
    price: float
    quantity: int

    model_config = ConfigDict(from_attributes=True)


class SubOrderTimelineOut(BaseModel):
    id: int
    status: str
    description: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SubOrderOut(BaseModel):
    id: int
    combined_order_id: int
    store_id: int
    store_name_snapshot: str
    items_total: float
    commission_rate: float
    status: str
    cancel_reason: str
    cancel_by: str
    accepted_at: Optional[datetime] = None
    ready_at: Optional[datetime] = None
    created_at: datetime
    items: List[SubOrderItemOut] = []
    store_name: str = ""

    model_config = ConfigDict(from_attributes=True)


class SubOrderDetailOut(SubOrderOut):
    timeline: List[SubOrderTimelineOut] = []


# ---- 总单输出 ----
class CombinedOrderOut(BaseModel):
    id: int
    order_no: str
    user_id: int
    address_snapshot: dict
    items_total: float
    delivery_fee_original: float
    delivery_fee_discount: float
    delivery_fee: float
    package_fee: float
    coupon_discount: float
    total_price: float
    status: str
    district_id: Optional[int]
    rider_id: Optional[int]
    user_coupon_id: Optional[int]
    remark: str
    paid_at: Optional[datetime] = None
    picked_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    delivery_photo: str = ""
    created_at: datetime
    sub_orders: List[SubOrderOut] = []
    rider_name: str = ""

    model_config = ConfigDict(from_attributes=True)


class CombinedOrderListOut(BaseModel):
    total: int
    items: List[CombinedOrderOut]


class CombinedOrderDetailOut(CombinedOrderOut):
    sub_orders: List[SubOrderDetailOut] = []


# ---- 评价 ----
class ReviewCreate(BaseModel):
    score: int = Field(..., ge=1, le=5)
    content: str = ""
    tags: List[str] = []


class ReviewOut(BaseModel):
    id: int
    sub_order_id: int
    user_id: int
    score: int
    content: str
    tags: List[str] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---- 订单修改申请 ----
class ModificationCreate(BaseModel):
    type: str = "cancel"  # cancel / address_change / refund / other
    reason: str = ""
    new_address: Optional[dict] = None


class ModificationOut(BaseModel):
    id: int
    combined_order_id: int
    sub_order_id: Optional[int] = None
    type: str
    reason: str
    new_address: Optional[dict] = None
    status: str
    reviewed_by: Optional[int] = None
    review_comment: str
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    # 关联信息
    order_no: str = ""
    store_name: str = ""
    user_name: str = ""
    items_total: float = 0

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# 旧 Schema — 兼容保留
# ============================================================

class OrderCreate(BaseModel):
    """[deprecated]"""
    store_id: int
    address_id: int
    items: List[OrderItemIn] = Field(..., min_length=1)
    remark: str = ""
    user_coupon_id: Optional[int] = None


class OrderOut(BaseModel):
    """[deprecated]"""
    id: int
    order_no: str
    user_id: int
    store_id: int
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
    paid_at: Optional[datetime] = None
    accepted_at: Optional[datetime] = None
    ready_at: Optional[datetime] = None
    picked_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    items: List[OrderItemOut] = []
    store_name: str = ""
    rider_name: str = ""

    model_config = ConfigDict(from_attributes=True)


class OrderListOut(BaseModel):
    """[deprecated]"""
    total: int
    items: List[OrderOut]


class TimelineOut(BaseModel):
    """[deprecated]"""
    id: int
    status: str
    description: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderDetailOut(OrderOut):
    """[deprecated]"""
    timeline: List[TimelineOut] = []
    review: Optional[dict] = None


class OrderMessageOut(BaseModel):
    """订单留言"""
    id: int
    combined_order_id: int
    sender_id: int
    sender_role: str
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderMessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=500)
