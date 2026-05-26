class TestMerchantOrderList:
    def test_list_orders(self, client, auth_header_merchant, sub_order, restaurant):
        """List sub_orders - returns sub_orders for merchant's store"""
        resp = client.get("/api/merchant/orders", headers=auth_header_merchant)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert item["store_id"] == restaurant.id

    def test_list_orders_with_status_filter(self, client, auth_header_merchant, sub_order, restaurant):
        """List sub_orders with status filter"""
        # sub_order is "pending_accept" by default
        resp = client.get("/api/merchant/orders?status=pending_accept", headers=auth_header_merchant)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert item["status"] == "pending_accept"

        # filter by a status that does not match any sub_order
        resp = client.get("/api/merchant/orders?status=completed", headers=auth_header_merchant)
        assert resp.status_code == 200
        assert resp.json()["total"] == 0


class TestMerchantOrderDetail:
    def test_get_order_detail_with_timeline(self, client, auth_header_merchant, sub_order, restaurant):
        """Get sub_order detail with timeline"""
        resp = client.get(f"/api/merchant/orders/{sub_order.id}", headers=auth_header_merchant)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == sub_order.id
        assert data["store_id"] == restaurant.id
        assert data["store_name"] == restaurant.name
        assert "timeline" in data
        assert "items" in data
        assert len(data["items"]) >= 1

    def test_get_order_from_other_restaurant_returns_404(
        self, client, auth_header_merchant, sub_order, db_session, restaurant, region
    ):
        """Get sub_order from another store returns 404"""
        from models.user import User
        from models.store import Store
        from models.order import CombinedOrder, SubOrder
        from auth import hash_password

        # Create a second merchant user
        other_merchant = User(
            openid="other_merchant_test", nickname="其他商家", role="merchant",
            phone="13900000099", hashed_password=hash_password("pass123"),
        )
        db_session.add(other_merchant)
        db_session.flush()

        # Create a second store for the other merchant
        other_store = Store(
            user_id=other_merchant.id, name="其他餐厅", phone="13900000099",
            address="其他地址某某路1号", category="其他", status="open",
            verify_status="verified", district_id=region.id,
        )
        db_session.add(other_store)
        db_session.flush()

        # Create a sub_order belonging to the other store
        co = CombinedOrder(
            order_no="OTHER20240101001",
            user_id=sub_order.combined_order.user_id,
            address_snapshot={"contact_name": "test", "contact_phone": "13800000000", "detail": "test"},
            items_total=10, delivery_fee_original=5, delivery_fee=5, total_price=15,
            status="pending", district_id=region.id,
        )
        db_session.add(co)
        db_session.flush()
        other_sub = SubOrder(
            combined_order_id=co.id, store_id=other_store.id,
            store_name_snapshot="其他餐厅", items_total=10, status="pending_accept",
        )
        db_session.add(other_sub)
        db_session.flush()

        # First merchant tries to access the other store's sub_order
        resp = client.get(f"/api/merchant/orders/{other_sub.id}", headers=auth_header_merchant)
        assert resp.status_code == 404


class TestMerchantOrderAccept:
    def test_accept_order(self, client, auth_header_merchant, sub_order, db_session):
        """Accept sub_order - changes status from pending_accept to preparing"""
        resp = client.put(f"/api/merchant/orders/{sub_order.id}/accept", headers=auth_header_merchant)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "preparing"
        assert data["accepted_at"] is not None

    def test_accept_order_wrong_status_returns_400(self, client, auth_header_merchant, sub_order, db_session):
        """Accept sub_order in wrong status returns 400"""
        sub_order.status = "preparing"
        db_session.flush()
        resp = client.put(f"/api/merchant/orders/{sub_order.id}/accept", headers=auth_header_merchant)
        assert resp.status_code == 400


class TestMerchantOrderReject:
    def test_reject_order(self, client, auth_header_merchant, sub_order, db_session):
        """Reject sub_order - changes status from pending_accept to cancelled"""
        resp = client.put(
            f"/api/merchant/orders/{sub_order.id}/reject?reason=太忙了",
            headers=auth_header_merchant,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "cancelled"
        assert data["cancel_by"] == "merchant"

    def test_reject_order_wrong_status_returns_400(self, client, auth_header_merchant, sub_order, db_session):
        """Reject sub_order in wrong status returns 400"""
        sub_order.status = "preparing"
        db_session.flush()
        resp = client.put(
            f"/api/merchant/orders/{sub_order.id}/reject?reason=太忙了",
            headers=auth_header_merchant,
        )
        assert resp.status_code == 400


class TestMerchantOrderReady:
    def test_mark_ready(self, client, auth_header_merchant, sub_order, db_session):
        """Mark sub_order ready for pickup - changes status from preparing to ready"""
        sub_order.status = "preparing"
        db_session.flush()
        resp = client.put(f"/api/merchant/orders/{sub_order.id}/ready", headers=auth_header_merchant)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ready"
        assert data["ready_at"] is not None

    def test_mark_ready_wrong_status_returns_400(self, client, auth_header_merchant, sub_order):
        """Mark ready in wrong status (pending_accept) returns 400"""
        resp = client.put(f"/api/merchant/orders/{sub_order.id}/ready", headers=auth_header_merchant)
        assert resp.status_code == 400
