from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from auth import require_user
from database import get_db
from models.restaurant import Restaurant
from schemas.restaurant import RestaurantOut, RestaurantDetailOut, RestaurantListOut

router = APIRouter(prefix="/api/user/restaurants", tags=["用户端-餐厅"])


@router.get("", response_model=RestaurantListOut)
def list_restaurants(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    category: str = Query(default=""),
    keyword: str = Query(default=""),
    region_id: int = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(Restaurant).filter(
        Restaurant.status == "open",
        Restaurant.verify_status == "verified",
    )
    if category:
        query = query.filter(Restaurant.category == category)
    if keyword:
        query = query.filter(Restaurant.name.contains(keyword))
    if region_id:
        query = query.filter(Restaurant.region_id == region_id)

    total = query.count()
    items = query.order_by(Restaurant.monthly_sales.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return RestaurantListOut(total=total, items=[RestaurantOut.model_validate(r) for r in items])


@router.get("/{restaurant_id}", response_model=RestaurantDetailOut)
def get_restaurant(
    restaurant_id: int,
    db: Session = Depends(get_db),
):
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="餐厅不存在")
    return RestaurantDetailOut.model_validate(restaurant)
