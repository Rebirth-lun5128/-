"""Tests for authentication: wechat login, phone login, phone register, get current user."""
import pytest


class TestWechatLogin:
    def test_wechat_login_new_user(self, client):
        """New user with valid code should auto-register and return token."""
        resp = client.post("/api/common/auth/wechat", json={"code": "test_code_abc123456789"})
        assert resp.status_code == 200
        data = resp.json()
        assert "token" in data
        assert data["user"]["role"] == "user"
        assert "mock_openid" in data["user"]["openid"]

    def test_wechat_login_same_code_returns_same_user(self, client):
        """Same code should return the same user (no duplicate registration)."""
        code = "test_repeat_user_12345678"
        resp1 = client.post("/api/common/auth/wechat", json={"code": code})
        assert resp1.status_code == 200
        user_id_1 = resp1.json()["user"]["id"]

        resp2 = client.post("/api/common/auth/wechat", json={"code": code})
        assert resp2.status_code == 200
        assert resp2.json()["user"]["id"] == user_id_1

    def test_wechat_login_empty_code(self, client):
        """Empty code should still work in mock mode."""
        resp = client.post("/api/common/auth/wechat", json={"code": ""})
        assert resp.status_code == 200
        data = resp.json()
        assert "token" in data


class TestPhoneLogin:
    def test_phone_login_success(self, client, test_user_merchant):
        """Valid phone + password should return token."""
        resp = client.post("/api/common/auth/phone", json={
            "phone": "13900000001", "password": "pass123"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "token" in data
        assert data["user"]["role"] == "merchant"

    def test_phone_login_wrong_password(self, client, test_user_merchant):
        """Wrong password should return 400."""
        resp = client.post("/api/common/auth/phone", json={
            "phone": "13900000001", "password": "wrongpassword"
        })
        assert resp.status_code == 400
        assert "密码错误" in resp.json()["detail"]

    def test_phone_login_unregistered(self, client):
        """Unregistered phone should return 400."""
        resp = client.post("/api/common/auth/phone", json={
            "phone": "19900000000", "password": "pass123"
        })
        assert resp.status_code == 400
        assert "未注册" in resp.json()["detail"]

    def test_phone_login_admin(self, client, test_user_admin):
        """Admin should be able to login."""
        resp = client.post("/api/common/auth/phone", json={
            "phone": "13800000000", "password": "admin123"
        })
        assert resp.status_code == 200
        assert resp.json()["user"]["role"] == "super_admin"


class TestPhoneRegister:
    def test_register_new_user(self, client):
        """New phone registration should succeed."""
        resp = client.post("/api/common/auth/register", json={
            "phone": "13911111111", "password": "mypassword"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "token" in data
        assert data["user"]["role"] == "merchant"

    def test_register_duplicate_phone(self, client, test_user_merchant):
        """Duplicate phone registration should fail."""
        resp = client.post("/api/common/auth/register", json={
            "phone": "13900000001", "password": "pass123"
        })
        assert resp.status_code == 400
        assert "已注册" in resp.json()["detail"]

    def test_register_then_login(self, client):
        """User should be able to login after registration."""
        phone, password = "13922222222", "securepass"
        reg_resp = client.post("/api/common/auth/register", json={
            "phone": phone, "password": password
        })
        assert reg_resp.status_code == 200

        login_resp = client.post("/api/common/auth/phone", json={
            "phone": phone, "password": password
        })
        assert login_resp.status_code == 200


class TestGetCurrentUser:
    def test_get_me_authenticated(self, client, auth_header):
        """Authenticated request should return user info."""
        resp = client.get("/api/common/auth/me", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()
        assert "nickname" in data
        assert "role" in data

    def test_get_me_no_token(self, client):
        """No token should return 403."""
        resp = client.get("/api/common/auth/me")
        assert resp.status_code == 403

    def test_get_me_invalid_token(self, client):
        """Invalid token should return 401."""
        resp = client.get("/api/common/auth/me", headers={"Authorization": "Bearer invalid_token"})
        assert resp.status_code == 401
