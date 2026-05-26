import pytest
from models.user import UserAddress


@pytest.fixture
def my_address(client, auth_header, db_session):
    """Create an address belonging to the currently authenticated user."""
    me = client.get("/api/common/auth/me", headers=auth_header)
    user_id = me.json()["id"]
    addr = UserAddress(
        user_id=user_id,
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


class TestUserAddressCRUD:
    def test_list_addresses(self, client, auth_header, my_address):
        """List user's addresses - should include the pre-created address."""
        res = client.get("/api/user/addresses", headers=auth_header)
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["contact_name"] == "张三"
        assert data[0]["detail"] == "测试路1号"
        assert data[0]["label"] == "家"
        assert data[0]["is_default"] == 1

    def test_create_address_all_fields(self, client, auth_header):
        """Create an address providing every field."""
        body = {
            "contact_name": "李四",
            "contact_phone": "13800002222",
            "gender": 2,
            "province": "广东省",
            "city": "深圳市",
            "district": "南山区",
            "detail": "科技园路88号",
            "lat": 22.543099,
            "lng": 113.952600,
            "label": "公司",
            "is_default": 0,
        }
        res = client.post("/api/user/addresses", json=body, headers=auth_header)
        assert res.status_code == 200
        data = res.json()
        assert data["contact_name"] == "李四"
        assert data["contact_phone"] == "13800002222"
        assert data["gender"] == 2
        assert data["detail"] == "科技园路88号"
        assert data["label"] == "公司"
        assert data["is_default"] == 0

    def test_create_address_as_default_clears_previous(self, client, auth_header, my_address):
        """When is_default=1, the previous default should be set to 0."""
        assert my_address.is_default == 1

        body = {
            "contact_name": "王五",
            "contact_phone": "13800003333",
            "detail": "新地址100号",
            "city": "广州市",
            "is_default": 1,
        }
        res = client.post("/api/user/addresses", json=body, headers=auth_header)
        assert res.status_code == 200
        assert res.json()["is_default"] == 1

        list_res = client.get("/api/user/addresses", headers=auth_header)
        addrs = list_res.json()
        assert addrs[0]["is_default"] == 1
        assert addrs[0]["contact_name"] == "王五"
        old_addr = next(a for a in addrs if a["id"] == my_address.id)
        assert old_addr["is_default"] == 0

    def test_update_address(self, client, auth_header, my_address):
        """Update own address - change contact_name."""
        res = client.put(
            f"/api/user/addresses/{my_address.id}",
            json={"contact_name": "张三改"},
            headers=auth_header,
        )
        assert res.status_code == 200
        assert res.json()["contact_name"] == "张三改"

    def test_update_address_set_as_default(self, client, auth_header, my_address, db_session):
        """Update a non-default address to become the default - previous default cleared."""
        me = client.get("/api/common/auth/me", headers=auth_header)
        user_id = me.json()["id"]
        addr2 = UserAddress(
            user_id=user_id,
            contact_name="赵六",
            contact_phone="13800004444",
            detail="备用地址",
            is_default=0,
        )
        db_session.add(addr2)
        db_session.flush()

        res = client.put(
            f"/api/user/addresses/{addr2.id}",
            json={"is_default": 1},
            headers=auth_header,
        )
        assert res.status_code == 200
        assert res.json()["is_default"] == 1

        list_res = client.get("/api/user/addresses", headers=auth_header)
        addrs = list_res.json()
        assert addrs[0]["id"] == addr2.id
        assert addrs[0]["is_default"] == 1
        old_default = next(a for a in addrs if a["id"] == my_address.id)
        assert old_default["is_default"] == 0

    def test_delete_address(self, client, auth_header, my_address):
        """Delete own address."""
        res = client.delete(f"/api/user/addresses/{my_address.id}", headers=auth_header)
        assert res.status_code == 200
        assert res.json()["message"] == "已删除"

        list_res = client.get("/api/user/addresses", headers=auth_header)
        ids = [a["id"] for a in list_res.json()]
        assert my_address.id not in ids

    def test_delete_nonexistent_address(self, client, auth_header):
        """Deleting an address that does not exist returns 404."""
        res = client.delete("/api/user/addresses/99999", headers=auth_header)
        assert res.status_code == 404
        assert res.json()["detail"] == "地址不存在"

    def test_cannot_update_another_user_address(self, client, auth_header, db_session):
        """Attempting to update/delete another user's address returns 404."""
        from models.user import User
        from auth import hash_password

        other_user = User(
            openid="other_user_addr_test",
            nickname="其他用户",
            role="user",
            phone="13999999999",
            hashed_password=hash_password("pass"),
            status=1,
        )
        db_session.add(other_user)
        db_session.flush()

        other_addr = UserAddress(
            user_id=other_user.id,
            contact_name="他人地址",
            contact_phone="13800009999",
            detail="别人的地址",
            is_default=1,
        )
        db_session.add(other_addr)
        db_session.flush()

        res = client.put(
            f"/api/user/addresses/{other_addr.id}",
            json={"contact_name": "被改"},
            headers=auth_header,
        )
        assert res.status_code == 404

        res = client.delete(f"/api/user/addresses/{other_addr.id}", headers=auth_header)
        assert res.status_code == 404

    def test_create_address_missing_required_fields(self, client, auth_header):
        """Pydantic validation: missing contact_name, contact_phone, detail returns 422."""
        body = {"city": "北京", "is_default": 0}
        res = client.post("/api/user/addresses", json=body, headers=auth_header)
        assert res.status_code == 422

    def test_unauthenticated_access(self, client):
        """No auth header should return 401."""
        res = client.get("/api/user/addresses")
        assert res.status_code == 403

    def test_wrong_role_access(self, client, auth_header_merchant):
        """Merchant role should be denied (only 'user' role allowed)."""
        res = client.get("/api/user/addresses", headers=auth_header_merchant)
        assert res.status_code == 403
