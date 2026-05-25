from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import require_merchant
from database import get_db
from models.user import User
from models.restaurant import Restaurant, MenuCategory, MenuItem
from schemas.restaurant import (
    MenuItemOut, MenuItemCreate, MenuItemUpdate,
    MenuCategoryOut, MenuCategoryCreate,
)

router = APIRouter(prefix="/api/merchant/menu", tags=["商家端-菜单"])


def _get_restaurant(user: User, db: Session) -> Restaurant:
    r = db.query(Restaurant).filter(Restaurant.user_id == user.id).first()
    if not r:
        raise HTTPException(status_code=404, detail="请先入驻")
    return r


# ---- 分类 ----
@router.get("/categories", response_model=list[MenuCategoryOut])
def list_categories(user: User = Depends(require_merchant), db: Session = Depends(get_db)):
    restaurant = _get_restaurant(user, db)
    return db.query(MenuCategory).filter(MenuCategory.restaurant_id == restaurant.id).order_by(MenuCategory.sort_order).all()


@router.post("/categories", response_model=MenuCategoryOut)
def create_category(body: MenuCategoryCreate, user: User = Depends(require_merchant), db: Session = Depends(get_db)):
    restaurant = _get_restaurant(user, db)
    cat = MenuCategory(restaurant_id=restaurant.id, **body.model_dump())
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


@router.delete("/categories/{category_id}")
def delete_category(category_id: int, user: User = Depends(require_merchant), db: Session = Depends(get_db)):
    restaurant = _get_restaurant(user, db)
    cat = db.query(MenuCategory).filter(MenuCategory.id == category_id, MenuCategory.restaurant_id == restaurant.id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="分类不存在")
    db.delete(cat)
    db.commit()
    return {"message": "已删除"}


# ---- 菜品 ----
@router.get("/items", response_model=list[MenuItemOut])
def list_items(
    category_id: int = None,
    user: User = Depends(require_merchant),
    db: Session = Depends(get_db),
):
    restaurant = _get_restaurant(user, db)
    query = db.query(MenuItem).filter(MenuItem.restaurant_id == restaurant.id)
    if category_id is not None:
        query = query.filter(MenuItem.category_id == category_id)
    return query.order_by(MenuItem.sort_order).all()


@router.post("/items", response_model=MenuItemOut)
def create_item(body: MenuItemCreate, user: User = Depends(require_merchant), db: Session = Depends(get_db)):
    restaurant = _get_restaurant(user, db)
    item = MenuItem(restaurant_id=restaurant.id, **body.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/items/{item_id}", response_model=MenuItemOut)
def update_item(item_id: int, body: MenuItemUpdate, user: User = Depends(require_merchant), db: Session = Depends(get_db)):
    restaurant = _get_restaurant(user, db)
    item = db.query(MenuItem).filter(MenuItem.id == item_id, MenuItem.restaurant_id == restaurant.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="菜品不存在")
    update_data = body.model_dump(exclude_unset=True)
    for key, val in update_data.items():
        setattr(item, key, val)
    db.commit()
    db.refresh(item)
    return item


@router.put("/items/{item_id}/status")
def toggle_item_status(item_id: int, status: int = 1, user: User = Depends(require_merchant), db: Session = Depends(get_db)):
    restaurant = _get_restaurant(user, db)
    item = db.query(MenuItem).filter(MenuItem.id == item_id, MenuItem.restaurant_id == restaurant.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="菜品不存在")
    item.status = status
    db.commit()
    return {"message": "已更新", "status": status}


@router.delete("/items/{item_id}")
def delete_item(item_id: int, user: User = Depends(require_merchant), db: Session = Depends(get_db)):
    restaurant = _get_restaurant(user, db)
    item = db.query(MenuItem).filter(MenuItem.id == item_id, MenuItem.restaurant_id == restaurant.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="菜品不存在")
    db.delete(item)
    db.commit()
    return {"message": "已删除"}
