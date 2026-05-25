class TestPendingOrders:
    def test_pending_orders_empty(self, client, auth_header_rider, rider, order):
        """List pending orders returns empty when no orders have status='ready'."""
        resp = client.get("/api/rider/orders/pending", headers=auth_header_rider)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []


class TestAcceptOrder:
    def test_accept_order(self, client, auth_header_rider, rider, order, db_session):
        """Accept a ready order; sets status to 'delivering' and assigns rider."""
        order.status = "ready"
        db_session.flush()

        resp = client.post(
            f"/api/rider/orders/{order.id}/accept", headers=auth_header_rider
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "delivering"
        assert data["rider_id"] == rider.id
        assert data["picked_at"] is not None
        assert data["rider_name"] == rider.real_name

    def test_accept_offline_rider(self, client, auth_header_rider, rider, order, db_session):
        """Offline rider cannot accept orders."""
        rider.status = "offline"
        order.status = "ready"
        db_session.flush()

        resp = client.post(
            f"/api/rider/orders/{order.id}/accept", headers=auth_header_rider
        )
        assert resp.status_code == 400

        # Restore for other tests
        rider.status = "online"
        db_session.flush()

    def test_accept_already_taken(self, client, auth_header_rider, rider, order, db_session):
        """Order already accepted (status != 'ready') returns 400."""
        order.status = "ready"
        db_session.flush()

        # First accept succeeds
        resp = client.post(
            f"/api/rider/orders/{order.id}/accept", headers=auth_header_rider
        )
        assert resp.status_code == 200

        # Second accept fails (order no longer 'ready')
        resp = client.post(
            f"/api/rider/orders/{order.id}/accept", headers=auth_header_rider
        )
        assert resp.status_code == 400


class TestMarkDelivered:
    def test_mark_delivered(self, client, auth_header_rider, rider, order, db_session):
        """Deliver an accepted order; status becomes 'completed', rider earns +5 balance."""
        order.status = "ready"
        db_session.flush()

        client.post(f"/api/rider/orders/{order.id}/accept", headers=auth_header_rider)

        resp = client.put(
            f"/api/rider/orders/{order.id}/deliver", headers=auth_header_rider
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"
        assert data["delivered_at"] is not None
        assert data["completed_at"] is not None

        db_session.refresh(rider)
        assert rider.status == "online"
        assert rider.total_orders == 51
        assert float(rider.balance) == 105.0

    def test_deliver_non_assigned_order(self, client, auth_header_rider, rider, order):
        """Cannot deliver an order not assigned to this rider."""
        resp = client.put(
            f"/api/rider/orders/{order.id}/deliver", headers=auth_header_rider
        )
        assert resp.status_code == 404


class TestMyOrders:
    def test_my_orders(self, client, auth_header_rider, rider, order, db_session):
        """After delivering, the order appears in the rider's history."""
        order.status = "ready"
        db_session.flush()

        client.post(f"/api/rider/orders/{order.id}/accept", headers=auth_header_rider)
        client.put(f"/api/rider/orders/{order.id}/deliver", headers=auth_header_rider)

        resp = client.get("/api/rider/orders/my", headers=auth_header_rider)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        ids = [o["id"] for o in data["items"]]
        assert order.id in ids


class TestRiderStatus:
    def test_update_status_offline_online(self, client, auth_header_rider, rider):
        """Update rider status to offline, then back to online."""
        resp = client.put(
            "/api/rider/orders/status?status=offline", headers=auth_header_rider
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "offline"

        resp = client.put(
            "/api/rider/orders/status?status=online", headers=auth_header_rider
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "online"

    def test_update_status_invalid(self, client, auth_header_rider, rider):
        """Invalid status value returns 400."""
        resp = client.put(
            "/api/rider/orders/status?status=invalid", headers=auth_header_rider
        )
        assert resp.status_code == 400


class TestRiderLocation:
    def test_update_location(self, client, auth_header_rider, rider):
        """Update rider GPS location."""
        resp = client.put(
            "/api/rider/orders/location?lat=39.9&lng=116.4", headers=auth_header_rider
        )
        assert resp.status_code == 200


class TestRiderWallet:
    def test_wallet(self, client, auth_header_rider, rider):
        """Wallet returns balance, total_orders, and rating."""
        resp = client.get("/api/rider/orders/wallet", headers=auth_header_rider)
        assert resp.status_code == 200
        data = resp.json()
        assert data["balance"] == 100.0
        assert data["total_orders"] == 50
        assert "rating" in data
