from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import require_merchant
from database import get_db
from models.user import User
from models.store import Store, StoreCategory, Product
from schemas.store import (
    ProductOut, ProductCreate, ProductUpdate,
    StoreCategoryOut, StoreCategoryCreate,
)

router = APIRouter(prefix="/api/merchant/menu", tags=["商家端-商品"])


def _get_store(user: User, db: Session) -> Store:
    s = db.query(Store).filter(Store.user_id == user.id).first()
    if not s:
        raise HTTPException(status_code=404, detail="请先入驻")
    return s


# ---- 分类 ----
@router.get("/categories", response_model=list[StoreCategoryOut])
def list_categories(user: User = Depends(require_merchant), db: Session = Depends(get_db)):
    store = _get_store(user, db)
    return db.query(StoreCategory).filter(StoreCategory.store_id == store.id).order_by(StoreCategory.sort_order).all()


@router.post("/categories", response_model=StoreCategoryOut)
def create_category(body: StoreCategoryCreate, user: User = Depends(require_merchant), db: Session = Depends(get_db)):
    store = _get_store(user, db)
    cat = StoreCategory(store_id=store.id, **body.model_dump())
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


@router.put("/categories/{category_id}")
def update_category(category_id: int, body: StoreCategoryCreate, user: User = Depends(require_merchant), db: Session = Depends(get_db)):
    store = _get_store(user, db)
    cat = db.query(StoreCategory).filter(StoreCategory.id == category_id, StoreCategory.store_id == store.id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="分类不存在")
    cat.name = body.name
    db.commit()
    db.refresh(cat)
    return cat


@router.put("/categories/sort")
def sort_categories(ids: list[int] = Body(...), user: User = Depends(require_merchant), db: Session = Depends(get_db)):
    """批量更新分类排序"""
    store = _get_store(user, db)
    for i, cid in enumerate(ids):
        cat = db.query(StoreCategory).filter(StoreCategory.id == cid, StoreCategory.store_id == store.id).first()
        if cat:
            cat.sort_order = i
    db.commit()
    return {"message": "排序已更新"}


@router.delete("/categories/{category_id}")
def delete_category(category_id: int, user: User = Depends(require_merchant), db: Session = Depends(get_db)):
    store = _get_store(user, db)
    cat = db.query(StoreCategory).filter(StoreCategory.id == category_id, StoreCategory.store_id == store.id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="分类不存在")
    db.delete(cat)
    db.commit()
    return {"message": "已删除"}


# ---- 商品 ----
@router.get("/items", response_model=list[ProductOut])
def list_products(
    category_id: int = None,
    user: User = Depends(require_merchant),
    db: Session = Depends(get_db),
):
    store = _get_store(user, db)
    query = db.query(Product).filter(Product.store_id == store.id)
    if category_id is not None:
        query = query.filter(Product.category_id == category_id)
    return query.order_by(Product.sort_order).all()


@router.post("/items", response_model=ProductOut)
def create_product(body: ProductCreate, user: User = Depends(require_merchant), db: Session = Depends(get_db)):
    store = _get_store(user, db)
    item = Product(store_id=store.id, **body.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/items/{item_id}", response_model=ProductOut)
def update_product(item_id: int, body: ProductUpdate, user: User = Depends(require_merchant), db: Session = Depends(get_db)):
    store = _get_store(user, db)
    item = db.query(Product).filter(Product.id == item_id, Product.store_id == store.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="商品不存在")
    update_data = body.model_dump(exclude_unset=True)
    for key, val in update_data.items():
        setattr(item, key, val)
    db.commit()
    db.refresh(item)
    return item


@router.put("/items/{item_id}/status")
def toggle_product_status(item_id: int, status: int = 1, user: User = Depends(require_merchant), db: Session = Depends(get_db)):
    store = _get_store(user, db)
    item = db.query(Product).filter(Product.id == item_id, Product.store_id == store.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="商品不存在")
    item.status = status
    db.commit()
    return {"message": "已更新", "status": status}


@router.delete("/items/{item_id}")
def delete_product(item_id: int, user: User = Depends(require_merchant), db: Session = Depends(get_db)):
    store = _get_store(user, db)
    item = db.query(Product).filter(Product.id == item_id, Product.store_id == store.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="商品不存在")
    db.delete(item)
    db.commit()
    return {"message": "已删除"}
