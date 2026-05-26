import os
import sys

# Must be set BEFORE any project imports
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import database
from database import Base, get_db
from auth import hash_password


# ---- Test engine (in-memory SQLite with StaticPool) ----
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


# Enable foreign keys for SQLite
@event.listens_for(test_engine, "connect")
def _enable_fk(dbapi_connection, connection_record):
    import sqlite3
    if isinstance(dbapi_connection, sqlite3.Connection):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")


# Override the project's engine and SessionLocal
database.engine = test_engine
database.SessionLocal = TestSessionLocal


# ---- Fixtures ----
@pytest.fixture(autouse=True)
def reset_db():
    """Create all tables before each test, drop after. Also reset rate limiters."""
    from ratelimit import general_limiter, strict_limiter
    if hasattr(general_limiter, "_hits"):
        general_limiter._hits.clear()
    if hasattr(strict_limiter, "_hits"):
        strict_limiter._hits.clear()
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    """SQLAlchemy session for seeding test data."""
    db = TestSessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@pytest.fixture
def client(db_session):
    """FastAPI TestClient with DB dependency overridden."""
    from main import app

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---- Seed data fixtures ----
@pytest.fixture
def region(db_session):
    from models.district import District
    r = District(id=1, name="测试区域", status=1)
    db_session.add(r)
    db_session.flush()
    return r


@pytest.fixture
def system_configs(db_session):
    from models.region import SystemConfig
    configs = [
        SystemConfig(config_key="platform_fee_rate", config_value="0.12", description="平台抽成比例"),
        SystemConfig(config_key="delivery_fee_default", config_value="5", description="默认配送费"),
        SystemConfig(config_key="rider_per_order", config_value="5", description="骑手每单收入"),
        SystemConfig(config_key="auto_cancel_minutes", config_value="15", description="自动取消时间"),
    ]
    for c in configs:
        db_session.add(c)
    db_session.flush()
    return configs


# ---- User fixtures ----
def _create_user(db_session, **kwargs):
    from models.user import User
    defaults = {"status": 1}
    defaults.update(kwargs)
    user = User(**defaults)
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def test_user_normal(db_session):
    return _create_user(db_session, openid="test_user_normal", nickname="测试用户", role="user")


@pytest.fixture
def test_user_merchant(db_session):
    return _create_user(db_session, openid="test_user_merchant", nickname="测试商家", role="merchant",
                        phone="13900000001", hashed_password=hash_password("pass123"))


@pytest.fixture
def test_user_rider(db_session):
    return _create_user(db_session, openid="test_user_rider", nickname="测试骑手", role="rider",
                        phone="13900000002", hashed_password=hash_password("pass123"))


@pytest.fixture
def test_user_admin(db_session):
    return _create_user(db_session, openid="test_user_admin", nickname="超级管理员", role="super_admin",
                        phone="13800000000", hashed_password=hash_password("admin123"))


@pytest.fixture
def test_user_district_admin(db_session, region):
    return _create_user(db_session, openid="test_district_admin", nickname="区域管理员", role="district_admin",
                        district_id=1, phone="13800000001", hashed_password=hash_password("admin123"))


# ---- Token helpers ----
def _get_token(client, phone, password="pass123"):
    resp = client.post("/api/common/auth/phone", json={"phone": phone, "password": password})
    if resp.status_code != 200:
        return None
    return resp.json()["token"]


@pytest.fixture
def auth_header(client, test_user_normal):
    """Authorization header for normal user (via wechat mock login)."""
    resp = client.post("/api/common/auth/wechat", json={"code": "test_code_1234567890"})
    token = resp.json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_header_merchant(client, test_user_merchant):
    token = _get_token(client, "13900000001", "pass123")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_header_rider(client, test_user_rider):
    token = _get_token(client, "13900000002", "pass123")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_header_admin(client, test_user_admin):
    token = _get_token(client, "13800000000", "admin123")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_header_district_admin(client, test_user_district_admin):
    token = _get_token(client, "13800000001", "admin123")
    return {"Authorization": f"Bearer {token}"}


# ---- Restaurant & Menu fixtures ----
@pytest.fixture
def restaurant(db_session, test_user_merchant, region):
    from models.store import Store
    r = Store(
        user_id=test_user_merchant.id,
        name="测试餐厅",
        phone="13900000001",
        address="测试地址123号",
        stall_location="A区12号摊位",
        category="烧烤",
        status="open",
        verify_status="verified",
        district_id=region.id,
        delivery_fee=5,
        min_price=20,
        business_hours={"open": "17:00", "close": "02:00"},
    )
    db_session.add(r)
    db_session.flush()
    return r


@pytest.fixture
def restaurant_unverified(db_session, test_user_merchant, region):
    from models.store import Store
    r = Store(
        user_id=test_user_merchant.id,
        name="待审核餐厅",
        phone="13900000001",
        address="测试地址456号",
        stall_location="B区3号摊位",
        category="小吃",
        status="closed",
        verify_status="unverified",
        district_id=region.id,
    )
    db_session.add(r)
    db_session.flush()
    return r


@pytest.fixture
def menu_category(db_session, restaurant):
    from models.store import StoreCategory
    c = StoreCategory(store_id=restaurant.id, name="招牌菜", sort_order=1)
    db_session.add(c)
    db_session.flush()
    return c


@pytest.fixture
def menu_items(db_session, restaurant, menu_category):
    from models.store import Product
    items = [
        Product(store_id=restaurant.id, category_id=menu_category.id, name="羊肉串", price=5, status=1, sort_order=1),
        Product(store_id=restaurant.id, category_id=menu_category.id, name="牛肉串", price=6, original_price=8, status=1, sort_order=2),
        Product(store_id=restaurant.id, category_id=menu_category.id, name="已下架菜品", price=10, status=0, sort_order=3),
    ]
    for item in items:
        db_session.add(item)
    db_session.flush()
    return items


# ---- Address fixture ----
@pytest.fixture
def address(db_session, test_user_normal):
    from models.user import UserAddress
    addr = UserAddress(
        user_id=test_user_normal.id,
        contact_name="张三",
        contact_phone="13800001111",
        gender=1,
        city="测试市",
        district="测试区",
        detail="测试路1号",
        label="家",
        is_default=1,
    )
    db_session.add(addr)
    db_session.flush()
    return addr


# ---- Rider fixture ----
@pytest.fixture
def rider(db_session, test_user_rider, region):
    from models.rider import Rider
    r = Rider(
        user_id=test_user_rider.id,
        real_name="李四",
        phone="13900000002",
        status="online",
        audit_status="approved",
        district_id=region.id,
        balance=100,
        total_orders=50,
    )
    db_session.add(r)
    db_session.flush()
    return r


# ---- Combined Order fixtures ----
@pytest.fixture
def combined_order(db_session, test_user_normal, restaurant, restaurant_unverified, address, region):
    """创建一个包含两个子单的合并订单"""
    from models.order import CombinedOrder, SubOrder, SubOrderItem, SubOrderTimeline
    order = CombinedOrder(
        order_no="COMBINED20240101001",
        user_id=test_user_normal.id,
        address_snapshot={
            "contact_name": address.contact_name,
            "contact_phone": address.contact_phone,
            "detail": address.detail,
        },
        items_total=27,
        delivery_fee_original=5,
        delivery_fee_discount=0,
        delivery_fee=5,
        total_price=32,
        status="pending",
        district_id=region.id if region else 1,
    )
    db_session.add(order)
    db_session.flush()

    # 子单1 - 已到ready状态
    sub1 = SubOrder(
        combined_order_id=order.id,
        store_id=restaurant.id,
        store_name_snapshot=restaurant.name,
        items_total=11,
        commission_rate=0.12,
        status="ready",
    )
    db_session.add(sub1)
    db_session.flush()
    db_session.add(SubOrderItem(sub_order_id=sub1.id, product_id=1, name="羊肉串", price=5, quantity=2))
    db_session.add(SubOrderItem(sub_order_id=sub1.id, product_id=2, name="牛肉串", price=6, quantity=1))
    db_session.add(SubOrderTimeline(sub_order_id=sub1.id, status="pending_accept", description="已支付"))
    db_session.add(SubOrderTimeline(sub_order_id=sub1.id, status="ready", description="已出餐"))

    # 子单2 - 也已ready
    sub2 = SubOrder(
        combined_order_id=order.id,
        store_id=restaurant_unverified.id,
        store_name_snapshot=restaurant_unverified.name,
        items_total=16,
        commission_rate=0.15,
        status="ready",
    )
    db_session.add(sub2)
    db_session.flush()
    db_session.add(SubOrderItem(sub_order_id=sub2.id, product_id=3, name="烤鸡翅", price=8, quantity=2))
    db_session.add(SubOrderTimeline(sub_order_id=sub2.id, status="pending_accept", description="已支付"))
    db_session.add(SubOrderTimeline(sub_order_id=sub2.id, status="ready", description="已出餐"))

    db_session.flush()
    return order


# ---- Order fixture (deprecated but retained for existing tests) ----
@pytest.fixture
def order(db_session, test_user_normal, restaurant, address):
    from models.order import Order, OrderItem
    order = Order(
        order_no="TEST20240101000001",
        user_id=test_user_normal.id,
        store_id=restaurant.id,
        address_snapshot={
            "contact_name": address.contact_name,
            "contact_phone": address.contact_phone,
            "detail": address.detail,
        },
        items_total=11,
        delivery_fee=5,
        total_price=16,
        status="pending_pay",
        district_id=1,
    )
    db_session.add(order)
    db_session.flush()
    item = OrderItem(order_id=order.id, product_id=1, name="羊肉串", price=5, quantity=2)
    db_session.add(item)
    item2 = OrderItem(order_id=order.id, product_id=2, name="牛肉串", price=6, quantity=1)
    db_session.add(item2)
    db_session.flush()
    return order


# ---- SubOrder fixture (for merchant tests) ----
@pytest.fixture
def sub_order(db_session, test_user_normal, restaurant, address, region):
    """创建一个属于restaurant的子单，CombinedOrder为pending_pay"""
    from models.order import CombinedOrder, SubOrder, SubOrderItem, SubOrderTimeline
    co = CombinedOrder(
        order_no="SUBORDER20240101001",
        user_id=test_user_normal.id,
        address_snapshot={
            "contact_name": address.contact_name,
            "contact_phone": address.contact_phone,
            "detail": address.detail,
        },
        items_total=11,
        delivery_fee_original=5,
        delivery_fee_discount=0,
        delivery_fee=5,
        total_price=16,
        status="pending",
        district_id=region.id,
    )
    db_session.add(co)
    db_session.flush()

    sub = SubOrder(
        combined_order_id=co.id,
        store_id=restaurant.id,
        store_name_snapshot=restaurant.name,
        items_total=11,
        commission_rate=0.12,
        status="pending_accept",
    )
    db_session.add(sub)
    db_session.flush()

    db_session.add(SubOrderItem(sub_order_id=sub.id, product_id=1, name="羊肉串", price=5, quantity=2))
    db_session.add(SubOrderItem(sub_order_id=sub.id, product_id=2, name="牛肉串", price=6, quantity=1))
    db_session.add(SubOrderTimeline(sub_order_id=sub.id, status="pending_accept", description="子单已创建，等待商家接单"))
    db_session.flush()
    return sub
