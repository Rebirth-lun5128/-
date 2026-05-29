"""管理后台 — 商品 & 分类管理（可管理任意店铺）"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from auth import require_any_admin
from database import get_db
from models.store import Store, StoreCategory, Product
from schemas.store import ProductCreate, ProductUpdate, ProductOut, StoreCategoryCreate, StoreCategoryOut

router = APIRouter(prefix="/api/admin", tags=["管理后台-商品"])


def _get_store_or_404(store_id: int, db: Session) -> Store:
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="店铺不存在")
    return store


# ==================== 分类 ====================

@router.get("/categories")
def list_categories(store_id: int = Query(...), db: Session = Depends(get_db), _=Depends(require_any_admin)):
    _get_store_or_404(store_id, db)
    cats = db.query(StoreCategory).filter(StoreCategory.store_id == store_id).order_by(StoreCategory.sort_order).all()
    return [StoreCategoryOut.model_validate(c).model_dump() for c in cats]


@router.post("/categories")
def create_category(body: StoreCategoryCreate, store_id: int = Query(...),
                    db: Session = Depends(get_db), _=Depends(require_any_admin)):
    _get_store_or_404(store_id, db)
    cat = StoreCategory(store_id=store_id, name=body.name, sort_order=body.sort_order)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return StoreCategoryOut.model_validate(cat).model_dump()


@router.put("/categories/{category_id}")
def update_category(category_id: int, body: StoreCategoryCreate,
                    db: Session = Depends(get_db), _=Depends(require_any_admin)):
    cat = db.query(StoreCategory).filter(StoreCategory.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="分类不存在")
    cat.name = body.name
    db.commit()
    return StoreCategoryOut.model_validate(cat).model_dump()


@router.delete("/categories/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_db), _=Depends(require_any_admin)):
    cat = db.query(StoreCategory).filter(StoreCategory.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="分类不存在")
    db.delete(cat)
    db.commit()
    return {"message": "已删除"}


# ==================== 商品 ====================

@router.get("/products")
def list_products(store_id: int = Query(...), category_id: int = Query(default=None),
                  db: Session = Depends(get_db), _=Depends(require_any_admin)):
    _get_store_or_404(store_id, db)
    q = db.query(Product).filter(Product.store_id == store_id)
    if category_id is not None:
        q = q.filter(Product.category_id == category_id)
    items = q.order_by(Product.sort_order, Product.id.desc()).all()
    return [ProductOut.model_validate(p).model_dump() for p in items]


@router.post("/products")
def create_product(body: ProductCreate, store_id: int = Query(...),
                   db: Session = Depends(get_db), _=Depends(require_any_admin)):
    _get_store_or_404(store_id, db)
    prod = Product(store_id=store_id, **body.model_dump())
    db.add(prod)
    db.commit()
    db.refresh(prod)
    return ProductOut.model_validate(prod).model_dump()


@router.put("/products/{product_id}")
def update_product(product_id: int, body: ProductUpdate,
                   db: Session = Depends(get_db), _=Depends(require_any_admin)):
    prod = db.query(Product).filter(Product.id == product_id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="商品不存在")
    for key, val in body.model_dump(exclude_unset=True).items():
        setattr(prod, key, val)
    db.commit()
    db.refresh(prod)
    return ProductOut.model_validate(prod).model_dump()


@router.put("/products/{product_id}/status")
def toggle_product_status(product_id: int, status: int = Query(default=1),
                          db: Session = Depends(get_db), _=Depends(require_any_admin)):
    prod = db.query(Product).filter(Product.id == product_id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="商品不存在")
    prod.status = status
    db.commit()
    return {"message": "已更新", "status": status}


@router.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db), _=Depends(require_any_admin)):
    prod = db.query(Product).filter(Product.id == product_id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="商品不存在")
    db.delete(prod)
    db.commit()
    return {"message": "已删除"}
