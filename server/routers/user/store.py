from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from auth import require_user
from database import get_db
from models.store import Store
from models.district import District
from schemas.store import StoreOut, StoreDetailOut, StoreListOut

router = APIRouter(prefix="/api/user/stores", tags=["用户端-店铺"])


@router.get("", response_model=StoreListOut)
def list_stores(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    category: str = Query(default=""),
    store_type: str = Query(default=""),
    keyword: str = Query(default=""),
    district_id: int = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(Store).filter(
        Store.status == "open",
        Store.verify_status == "verified",
    )
    if category:
        query = query.filter(Store.category == category)
    if store_type:
        query = query.filter(Store.store_type == store_type)
    if keyword:
        query = query.filter(Store.name.contains(keyword))
    if district_id:
        query = query.filter(Store.district_id == district_id)

    total = query.count()
    items = query.order_by(Store.monthly_sales.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return StoreListOut(total=total, items=[StoreOut.model_validate(r) for r in items])


@router.get("/districts/list")
def list_districts(db: Session = Depends(get_db)):
    """用户端可用分区列表"""
    districts = db.query(District).filter(District.status == 1).order_by(District.id).all()
    return [{"id": d.id, "name": d.name} for d in districts]


@router.get("/{store_id}", response_model=StoreDetailOut)
def get_store(
    store_id: int,
    db: Session = Depends(get_db),
):
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="店铺不存在")
    return StoreDetailOut.model_validate(store)
