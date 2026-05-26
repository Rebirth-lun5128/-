from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


# ---- Address ----
class AddressCreate(BaseModel):
    contact_name: str = Field(..., min_length=1, max_length=50)
    contact_phone: str = Field(..., min_length=1, max_length=20)
    gender: int = Field(default=1, ge=1, le=2)
    province: str = ""
    city: str = ""
    district: str = ""
    detail: str = Field(..., min_length=1, max_length=200)
    lat: Optional[float] = None
    lng: Optional[float] = None
    label: str = ""
    is_default: int = 0


class AddressUpdate(BaseModel):
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    gender: Optional[int] = None
    province: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    detail: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    label: Optional[str] = None
    is_default: Optional[int] = None


class AddressOut(BaseModel):
    id: int
    user_id: int
    contact_name: str
    contact_phone: str
    gender: int
    province: str
    city: str
    district: str
    detail: str
    lat: Optional[float]
    lng: Optional[float]
    label: str
    is_default: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---- User ----
class UserOut(BaseModel):
    id: int
    openid: str
    nickname: str
    avatar: str
    phone: str
    role: str
    district_id: Optional[int]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    phone: Optional[str] = None


# ---- Auth ----
class WechatLoginIn(BaseModel):
    code: str = Field(..., description="微信 wx.login 返回的 code")


class PhoneLoginIn(BaseModel):
    phone: str
    password: str
    role: str = "merchant"  # "merchant" or "rider"


class LoginOut(BaseModel):
    token: str
    user: UserOut
