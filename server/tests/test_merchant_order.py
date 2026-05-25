class TestMerchantOrderList:
    def test_list_orders(self, client, auth_header_merchant, order, restaurant):
        """List orders - returns orders for merchant's restaurant"""
        resp = client.get("/api/merchant/orders", headers=auth_header_merchant)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert item["restaurant_id"] == restaurant.id

    def test_list_orders_with_status_filter(self, client, auth_header_merchant, order, restaurant):
        """List orders with status filter"""
        # order is "pending_pay" by default
        resp = client.get("/api/merchant/orders?status=pending_pay", headers=auth_header_merchant)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert item["status"] == "pending_pay"

        # filter by a status that does not match any order
        resp = client.get("/api/merchant/orders?status=completed", headers=auth_header_merchant)
        assert resp.status_code == 200
        assert resp.json()["total"] == 0


class TestMerchantOrderDetail:
    def test_get_order_detail_with_timeline(self, client, auth_header_merchant, order, restaurant):
        """Get order detail with timeline"""
        resp = client.get(f"/api/merchant/orders/{order.id}", headers=auth_header_merchant)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == order.id
        assert data["restaurant_id"] == restaurant.id
        assert data["restaurant_name"] == restaurant.name
        assert "timeline" in data
        assert "items" in data
        assert len(data["items"]) >= 1

    def test_get_order_from_other_restaurant_returns_404(
        self, client, auth_header_merchant, order, db_session, restaurant, region
    ):
        """Get order from another restaurant returns 404"""
        from models.user import User
        from models.restaurant import Restaurant
        from models.order import Order
        from auth import hash_password

        # Create a second merchant user
        other_merchant = User(
            openid="other_merchant_test", nickname="其他商家", role="merchant",
            phone="13900000099", hashed_password=hash_password("pass123"),
        )
        db_session.add(other_merchant)
        db_session.flush()

        # Create a second restaurant for the other merchant
        other_restaurant = Restaurant(
            user_id=other_merchant.id, name="其他餐厅", phone="13900000099",
            address="其他地址某某路1号", category="其他", status="open",
            verify_status="verified", region_id=region.id,
        )
        db_session.add(other_restaurant)
        db_session.flush()

        # Create an order belonging to the other restaurant
        other_order = Order(
            order_no="OTHER20240101000001",
            user_id=order.user_id,
            restaurant_id=other_restaurant.id,
            address_snapshot={"contact_name": "test", "contact_phone": "13800000000", "detail": "test"},
            items_total=10, delivery_fee=5, total_price=15,
            status="pending_pay", region_id=region.id,
        )
        db_session.add(other_order)
        db_session.flush()

        # First merchant tries to access the other restaurant's order
        resp = client.get(f"/api/merchant/orders/{other_order.id}", headers=auth_header_merchant)
        assert resp.status_code == 404


class TestMerchantOrderAccept:
    def test_accept_order(self, client, auth_header_merchant, order, db_session):
        """Accept order - set to pending_accept first, then accept"""
        order.status = "pending_accept"
        db_session.flush()
        resp = client.put(f"/api/merchant/orders/{order.id}/accept", headers=auth_header_merchant)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "preparing"
        assert data["accepted_at"] is not None

    def test_accept_order_wrong_status_returns_400(self, client, auth_header_merchant, order):
        """Accept order in wrong status (pending_pay) returns 400"""
        resp = client.put(f"/api/merchant/orders/{order.id}/accept", headers=auth_header_merchant)
        assert resp.status_code == 400


class TestMerchantOrderReject:
    def test_reject_order(self, client, auth_header_merchant, order, db_session):
        """Reject order - set to pending_accept first, then reject with reason"""
        order.status = "pending_accept"
        db_session.flush()
        resp = client.put(
            f"/api/merchant/orders/{order.id}/reject?reason=太忙了",
            headers=auth_header_merchant,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "cancelled"
        assert data["cancel_by"] == "merchant"

    def test_reject_order_wrong_status_returns_400(self, client, auth_header_merchant, order):
        """Reject order in wrong status (pending_pay) returns 400"""
        resp = client.put(
            f"/api/merchant/orders/{order.id}/reject?reason=太忙了",
            headers=auth_header_merchant,
        )
        assert resp.status_code == 400


class TestMerchantOrderReady:
    def test_mark_ready(self, client, auth_header_merchant, order, db_session):
        """Mark order ready for pickup - set to preparing first, then mark ready"""
        order.status = "preparing"
        db_session.flush()
        resp = client.put(f"/api/merchant/orders/{order.id}/ready", headers=auth_header_merchant)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ready"
        assert data["ready_at"] is not None

    def test_mark_ready_wrong_status_returns_400(self, client, auth_header_merchant, order):
        """Mark ready in wrong status (pending_pay) returns 400"""
        resp = client.put(f"/api/merchant/orders/{order.id}/ready", headers=auth_header_merchant)
        assert resp.status_code == 400
