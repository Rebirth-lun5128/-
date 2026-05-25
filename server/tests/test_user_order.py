import pytest

from models.user import UserAddress


# ---- Helper: create address for the authenticated user ----
@pytest.fixture
def my_address(client, auth_header, db_session):
    """Create an address belonging to the currently authenticated user."""
    me = client.get("/api/common/auth/me", headers=auth_header)
    user_id = me.json()["id"]
    addr = UserAddress(
        user_id=user_id,
        contact_name="测试联系人",
        contact_phone="13800000000",
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


# ---- Test: Create Order ----
class TestCreateOrder:
    def test_success(self, client, auth_header, db_session, restaurant, menu_items, my_address):
        """Create order with items that meet min_price (>=20)."""
        item1, item2, _ = menu_items  # 羊肉串 5, 牛肉串 6
        body = {
            "restaurant_id": restaurant.id,
            "address_id": my_address.id,
            "items": [
                {"menu_item_id": item1.id, "name": item1.name, "price": float(item1.price), "quantity": 3},
                {"menu_item_id": item2.id, "name": item2.name, "price": float(item2.price), "quantity": 1},
            ],
            "remark": "少放辣",
        }
        # items_total = 5*3 + 6*1 = 21 >= min_price(20)
        res = client.post("/api/user/orders", json=body, headers=auth_header)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "pending_pay"
        assert data["order_no"] != ""
        assert data["items_total"] == 21.0
        assert data["total_price"] == 21.0 + float(restaurant.delivery_fee) + 1.0
        assert len(data["items"]) == 2
        assert data["restaurant_name"] == restaurant.name
        assert data["remark"] == "少放辣"

    def test_below_min_price(self, client, auth_header, db_session, restaurant, menu_items, my_address):
        """Order with items_total < restaurant.min_price returns 400."""
        item1, _, _ = menu_items  # 羊肉串 5
        body = {
            "restaurant_id": restaurant.id,
            "address_id": my_address.id,
            "items": [
                {"menu_item_id": item1.id, "name": item1.name, "price": float(item1.price), "quantity": 1},
            ],
        }
        # items_total = 5 < min_price(20)
        res = client.post("/api/user/orders", json=body, headers=auth_header)
        assert res.status_code == 400
        assert "起送价" in res.json()["detail"]

    def test_invalid_restaurant(self, client, auth_header, menu_items):
        """Non-existent restaurant returns 400."""
        item1, _, _ = menu_items
        body = {
            "restaurant_id": 99999,
            "address_id": 99999,
            "items": [
                {"menu_item_id": item1.id, "name": item1.name, "price": float(item1.price), "quantity": 1},
            ],
        }
        res = client.post("/api/user/orders", json=body, headers=auth_header)
        assert res.status_code == 400
        assert res.json()["detail"] == "餐厅不可用"

    def test_invalid_address(self, client, auth_header, restaurant, menu_items):
        """Address that does not exist returns 400."""
        item1, item2, _ = menu_items
        body = {
            "restaurant_id": restaurant.id,
            "address_id": 99999,
            "items": [
                {"menu_item_id": item1.id, "name": item1.name, "price": float(item1.price), "quantity": 3},
                {"menu_item_id": item2.id, "name": item2.name, "price": float(item2.price), "quantity": 1},
            ],
        }
        res = client.post("/api/user/orders", json=body, headers=auth_header)
        assert res.status_code == 400
        assert res.json()["detail"] == "地址不存在"

    def test_disabled_menu_item(self, client, auth_header, db_session, restaurant, menu_items, my_address):
        """Order containing a disabled (status=0) menu item returns 400."""
        _, _, disabled = menu_items  # 已下架菜品 status=0
        body = {
            "restaurant_id": restaurant.id,
            "address_id": my_address.id,
            "items": [
                {"menu_item_id": disabled.id, "name": disabled.name, "price": float(disabled.price), "quantity": 1},
            ],
        }
        res = client.post("/api/user/orders", json=body, headers=auth_header)
        assert res.status_code == 400
        assert "已下架" in res.json()["detail"]


# ---- Test: Pay Order ----
class TestPayOrder:
    def test_success(self, client, auth_header, db_session, restaurant, menu_items, my_address):
        """Pay returns isMock=True and auto-advances order to pending_accept."""
        item1, item2, _ = menu_items
        body = {
            "restaurant_id": restaurant.id,
            "address_id": my_address.id,
            "items": [
                {"menu_item_id": item1.id, "name": item1.name, "price": float(item1.price), "quantity": 3},
                {"menu_item_id": item2.id, "name": item2.name, "price": float(item2.price), "quantity": 1},
            ],
        }
        create = client.post("/api/user/orders", json=body, headers=auth_header)
        order_id = create.json()["id"]

        res = client.post(f"/api/user/orders/{order_id}/pay", headers=auth_header)
        assert res.status_code == 200
        data = res.json()
        assert data["isMock"] is True
        assert "appId" in data
        assert "package" in data

        # Verify order status advanced to pending_accept
        detail = client.get(f"/api/user/orders/{order_id}", headers=auth_header)
        assert detail.json()["status"] == "pending_accept"
        assert detail.json()["paid_at"] is not None

    def test_already_paid(self, client, auth_header, db_session, restaurant, menu_items, my_address):
        """Paying an already paid order returns 400."""
        item1, item2, _ = menu_items
        body = {
            "restaurant_id": restaurant.id,
            "address_id": my_address.id,
            "items": [
                {"menu_item_id": item1.id, "name": item1.name, "price": float(item1.price), "quantity": 3},
                {"menu_item_id": item2.id, "name": item2.name, "price": float(item2.price), "quantity": 1},
            ],
        }
        create = client.post("/api/user/orders", json=body, headers=auth_header)
        order_id = create.json()["id"]

        # First pay succeeds
        client.post(f"/api/user/orders/{order_id}/pay", headers=auth_header)
        # Second pay returns 400
        res = client.post(f"/api/user/orders/{order_id}/pay", headers=auth_header)
        assert res.status_code == 400


# ---- Test: Cancel Order ----
class TestCancelOrder:
    def test_cancel_from_pending_pay(self, client, auth_header, db_session, restaurant, menu_items, my_address):
        """Cancel an order that is in pending_pay status."""
        item1, item2, _ = menu_items
        body = {
            "restaurant_id": restaurant.id,
            "address_id": my_address.id,
            "items": [
                {"menu_item_id": item1.id, "name": item1.name, "price": float(item1.price), "quantity": 3},
                {"menu_item_id": item2.id, "name": item2.name, "price": float(item2.price), "quantity": 1},
            ],
        }
        create = client.post("/api/user/orders", json=body, headers=auth_header)
        order_id = create.json()["id"]

        res = client.put(f"/api/user/orders/{order_id}/cancel?reason=不想要了", headers=auth_header)
        assert res.status_code == 200
        assert res.json()["status"] == "cancelled"
        assert res.json()["cancel_by"] == "user"
        assert "不想要了" in res.json()["cancel_reason"]

    def test_cancel_from_pending_accept(self, client, auth_header, db_session, restaurant, menu_items, my_address):
        """Cancel an order that is in pending_accept status (after payment)."""
        item1, item2, _ = menu_items
        body = {
            "restaurant_id": restaurant.id,
            "address_id": my_address.id,
            "items": [
                {"menu_item_id": item1.id, "name": item1.name, "price": float(item1.price), "quantity": 3},
                {"menu_item_id": item2.id, "name": item2.name, "price": float(item2.price), "quantity": 1},
            ],
        }
        create = client.post("/api/user/orders", json=body, headers=auth_header)
        order_id = create.json()["id"]
        # Pay to advance to pending_accept
        client.post(f"/api/user/orders/{order_id}/pay", headers=auth_header)

        res = client.put(f"/api/user/orders/{order_id}/cancel?reason=等太久了", headers=auth_header)
        assert res.status_code == 200
        assert res.json()["status"] == "cancelled"
        assert res.json()["cancel_by"] == "user"


# ---- Test: Refund Order ----
class TestRefundOrder:
    def test_refund_from_pending_accept(self, client, auth_header, db_session, restaurant, menu_items, my_address):
        """Refund an order from pending_accept status."""
        item1, item2, _ = menu_items
        body = {
            "restaurant_id": restaurant.id,
            "address_id": my_address.id,
            "items": [
                {"menu_item_id": item1.id, "name": item1.name, "price": float(item1.price), "quantity": 3},
                {"menu_item_id": item2.id, "name": item2.name, "price": float(item2.price), "quantity": 1},
            ],
        }
        create = client.post("/api/user/orders", json=body, headers=auth_header)
        order_id = create.json()["id"]
        # Pay to advance to pending_accept
        client.post(f"/api/user/orders/{order_id}/pay", headers=auth_header)

        res = client.post(f"/api/user/orders/{order_id}/refund?reason=不想要了", headers=auth_header)
        assert res.status_code == 200
        assert res.json()["status"] == "cancelled"


# ---- Test: List Orders ----
class TestListOrders:
    def test_pagination(self, client, auth_header, db_session, restaurant, menu_items, my_address):
        """List orders with pagination returns correct page size."""
        item1, item2, _ = menu_items
        body = {
            "restaurant_id": restaurant.id,
            "address_id": my_address.id,
            "items": [
                {"menu_item_id": item1.id, "name": item1.name, "price": float(item1.price), "quantity": 3},
                {"menu_item_id": item2.id, "name": item2.name, "price": float(item2.price), "quantity": 1},
            ],
        }
        # Create 2 orders
        client.post("/api/user/orders", json=body, headers=auth_header)
        client.post("/api/user/orders", json=body, headers=auth_header)

        res = client.get("/api/user/orders?page=1&page_size=1", headers=auth_header)
        assert res.status_code == 200
        data = res.json()
        assert data["total"] >= 2
        assert len(data["items"]) == 1

    def test_status_filter(self, client, auth_header, db_session, restaurant, menu_items, my_address):
        """List orders filtered by status returns only matching orders."""
        item1, item2, _ = menu_items
        body = {
            "restaurant_id": restaurant.id,
            "address_id": my_address.id,
            "items": [
                {"menu_item_id": item1.id, "name": item1.name, "price": float(item1.price), "quantity": 3},
                {"menu_item_id": item2.id, "name": item2.name, "price": float(item2.price), "quantity": 1},
            ],
        }
        # Create one order and pay it (status -> pending_accept)
        create = client.post("/api/user/orders", json=body, headers=auth_header)
        client.post(f"/api/user/orders/{create.json()['id']}/pay", headers=auth_header)
        # Create another order (stays pending_pay)
        client.post("/api/user/orders", json=body, headers=auth_header)

        res = client.get("/api/user/orders?status=pending_accept", headers=auth_header)
        assert res.status_code == 200
        items = res.json()["items"]
        assert len(items) >= 1
        for item in items:
            assert item["status"] == "pending_accept"


# ---- Test: Order Detail ----
class TestOrderDetail:
    def test_get_detail_with_timeline(self, client, auth_header, db_session, restaurant, menu_items, my_address):
        """Get order detail returns timeline and items."""
        item1, item2, _ = menu_items
        body = {
            "restaurant_id": restaurant.id,
            "address_id": my_address.id,
            "items": [
                {"menu_item_id": item1.id, "name": item1.name, "price": float(item1.price), "quantity": 3},
                {"menu_item_id": item2.id, "name": item2.name, "price": float(item2.price), "quantity": 1},
            ],
        }
        create = client.post("/api/user/orders", json=body, headers=auth_header)
        order_id = create.json()["id"]

        res = client.get(f"/api/user/orders/{order_id}", headers=auth_header)
        assert res.status_code == 200
        data = res.json()
        assert len(data["timeline"]) >= 1
        assert data["timeline"][0]["status"] == "pending_pay"
        assert data["timeline"][0]["description"] == "订单已创建，等待支付"
        assert len(data["items"]) == 2
        assert data["restaurant_name"] == restaurant.name

    def test_not_found(self, client, auth_header):
        """Getting a non-existent order returns 404."""
        res = client.get("/api/user/orders/99999", headers=auth_header)
        assert res.status_code == 404
        assert res.json()["detail"] == "订单不存在"


# ---- Test: Rider Location ----
class TestRiderLocation:
    def test_not_delivering(self, client, auth_header, db_session, restaurant, menu_items, my_address):
        """Getting rider location when order is not delivering returns 400."""
        item1, item2, _ = menu_items
        body = {
            "restaurant_id": restaurant.id,
            "address_id": my_address.id,
            "items": [
                {"menu_item_id": item1.id, "name": item1.name, "price": float(item1.price), "quantity": 3},
                {"menu_item_id": item2.id, "name": item2.name, "price": float(item2.price), "quantity": 1},
            ],
        }
        create = client.post("/api/user/orders", json=body, headers=auth_header)
        order_id = create.json()["id"]

        res = client.get(f"/api/user/orders/{order_id}/rider-location", headers=auth_header)
        assert res.status_code == 400
        assert res.json()["detail"] == "骑手尚未取餐"
