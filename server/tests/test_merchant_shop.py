import pytest


class TestMerchantShop:
    """Tests for /api/merchant/shop endpoints"""

    def test_get_shop(self, client, auth_header_merchant, restaurant):
        """Get current merchant's shop returns restaurant data."""
        res = client.get("/api/merchant/shop", headers=auth_header_merchant)
        assert res.status_code == 200
        data = res.json()
        assert data["name"] == restaurant.name
        assert data["status"] == restaurant.status
        assert data["verify_status"] == restaurant.verify_status
        assert data["delivery_fee"] == float(restaurant.delivery_fee)
        assert data["category"] == restaurant.category
        assert data["address"] == restaurant.address

    def test_get_shop_not_registered(self, client, db_session, region):
        """GET shop when not registered returns 404."""
        from auth import hash_password, create_access_token
        from models.user import User

        user = User(
            openid="test_shop_no_rest",
            phone="13940000102",
            nickname="无店铺商家",
            hashed_password=hash_password("test123"),
            role="merchant",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        token = create_access_token(data={"sub": user.id, "role": "merchant"})
        headers = {"Authorization": f"Bearer {token}"}

        res = client.get("/api/merchant/shop", headers=headers)
        assert res.status_code == 404

    def test_register_shop(self, client, db_session, region):
        """Register a new shop with a fresh merchant user."""
        from auth import hash_password, create_access_token
        from models.user import User

        user = User(
            openid="test_shop_new_1",
            phone="13940000101",
            nickname="新商家",
            hashed_password=hash_password("test123"),
            role="merchant",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        token = create_access_token(data={"sub": user.id, "role": "merchant"})
        headers = {"Authorization": f"Bearer {token}"}

        body = {
            "name": "新开餐厅",
            "phone": "13940000101",
            "address": "北京朝阳区某某街",
            "category": "夜市小吃",
            "stall_location": "A区3号摊位",
        }
        res = client.post("/api/merchant/shop/register", json=body, headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["name"] == "新开餐厅"
        assert data["verify_status"] == "unverified"
        assert data["status"] == "closed"

    def test_register_shop_duplicate(self, client, auth_header_merchant, restaurant):
        """Register shop when already registered returns 400."""
        body = {
            "name": "重复注册",
            "address": "X",
            "category": "Y",
        }
        res = client.post("/api/merchant/shop/register", json=body, headers=auth_header_merchant)
        assert res.status_code == 400

    def test_update_shop(self, client, auth_header_merchant, restaurant):
        """Update shop name and notice."""
        res = client.put(
            "/api/merchant/shop",
            json={"name": "改名了", "notice": "营业时间调整"},
            headers=auth_header_merchant,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["name"] == "改名了"
        assert data["notice"] == "营业时间调整"

    def test_dashboard(self, client, auth_header_merchant, restaurant):
        """Dashboard returns today_orders, today_revenue, pending_orders, etc."""
        res = client.get("/api/merchant/shop/dashboard", headers=auth_header_merchant)
        assert res.status_code == 200
        data = res.json()
        assert "today_orders" in data
        assert "today_revenue" in data
        assert "pending_orders" in data
        assert "monthly_sales" in data
        assert "rating" in data
        assert "status" in data
        assert "verify_status" in data

    def test_settlement(self, client, auth_header_merchant, restaurant, system_configs):
        """Settlement returns revenue data with records list."""
        res = client.get("/api/merchant/shop/settlement", headers=auth_header_merchant)
        assert res.status_code == 200
        data = res.json()
        assert "total_revenue" in data
        assert "total_orders" in data
        assert "fee_rate" in data
        assert "platform_fee" in data
        assert "net_revenue" in data
        assert "settled_amount" in data
        assert "pending_settlement" in data
        assert "records" in data
        assert isinstance(data["records"], list)
