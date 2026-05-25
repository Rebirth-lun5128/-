from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import require_user, get_current_user
from database import get_db
from models.user import User, UserAddress
from schemas.user import AddressCreate, AddressUpdate, AddressOut

router = APIRouter(prefix="/api/user/addresses", tags=["用户端-地址"])


@router.get("", response_model=List[AddressOut])
def list_addresses(
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    return db.query(UserAddress).filter(UserAddress.user_id == user.id).order_by(UserAddress.is_default.desc()).all()


@router.post("", response_model=AddressOut)
def create_address(
    body: AddressCreate,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    if body.is_default:
        db.query(UserAddress).filter(UserAddress.user_id == user.id).update({"is_default": 0})
    addr = UserAddress(user_id=user.id, **body.model_dump())
    db.add(addr)
    db.commit()
    db.refresh(addr)
    return addr


@router.put("/{address_id}", response_model=AddressOut)
def update_address(
    address_id: int,
    body: AddressUpdate,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    addr = db.query(UserAddress).filter(UserAddress.id == address_id, UserAddress.user_id == user.id).first()
    if not addr:
        raise HTTPException(status_code=404, detail="地址不存在")
    update_data = body.model_dump(exclude_unset=True)
    if update_data.get("is_default"):
        db.query(UserAddress).filter(UserAddress.user_id == user.id).update({"is_default": 0})
    for key, val in update_data.items():
        setattr(addr, key, val)
    db.commit()
    db.refresh(addr)
    return addr


@router.delete("/{address_id}")
def delete_address(
    address_id: int,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    addr = db.query(UserAddress).filter(UserAddress.id == address_id, UserAddress.user_id == user.id).first()
    if not addr:
        raise HTTPException(status_code=404, detail="地址不存在")
    db.delete(addr)
    db.commit()
    return {"message": "已删除"}
