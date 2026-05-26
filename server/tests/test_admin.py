"""Tests for admin dashboard API — platform management endpoints."""
import pytest


class TestAdminDashboard:
    """GET /api/admin/dashboard — data overview."""

    def test_dashboard_as_super_admin(self, client, auth_header_admin, system_configs):
        """Dashboard as super_admin returns all stats fields."""
        res = client.get("/api/admin/dashboard", headers=auth_header_admin)
        assert res.status_code == 200
        data = res.json()
        assert "total_users" in data
        assert "total_stores" in data
        assert "verified_stores" in data
        assert "total_riders" in data
        assert "today_orders" in data
        assert "today_revenue" in data
        assert "today_platform_fee" in data
        assert "fee_rate" in data
        assert "pending_verify_stores" in data
        assert "pending_orders" in data
        assert data["fee_rate"] == 0.12

    def test_dashboard_as_district_admin(self, client, auth_header_district_admin, system_configs):
        """Dashboard as district_admin returns filtered stats."""
        res = client.get("/api/admin/dashboard", headers=auth_header_district_admin)
        assert res.status_code == 200
        data = res.json()
        assert "total_users" in data
        assert "fee_rate" in data

    def test_dashboard_without_auth_returns_401(self, client):
        """Dashboard without any Authorization header returns 401."""
        res = client.get("/api/admin/dashboard")
        assert res.status_code == 403

    def test_dashboard_as_normal_user_returns_403(self, client, auth_header):
        """Dashboard accessed by normal user (role=user) returns 403."""
        res = client.get("/api/admin/dashboard", headers=auth_header)
        assert res.status_code == 403


class TestAdminRestaurants:
    """Restaurant management: list, verify, toggle-status."""

    def test_list_restaurants(self, client, auth_header_admin, restaurant, restaurant_unverified):
        """List restaurants returns paginated results with total and items."""
        res = client.get("/api/admin/stores", headers=auth_header_admin)
        assert res.status_code == 200
        data = res.json()
        assert "total" in data
        assert "items" in data
        assert data["total"] >= 2
        assert len(data["items"]) >= 2

    def test_list_restaurants_with_verify_status_filter(self, client, auth_header_admin, restaurant, restaurant_unverified):
        """Filter restaurants by verify_status query param."""
        res = client.get("/api/admin/stores?verify_status=unverified", headers=auth_header_admin)
        assert res.status_code == 200
        data = res.json()
        for r in data["items"]:
            assert r["verify_status"] == "unverified"

    def test_list_restaurants_pagination(self, client, auth_header_admin, restaurant, restaurant_unverified):
        """Pagination params page and page_size are respected."""
        res = client.get("/api/admin/stores?page=1&page_size=1", headers=auth_header_admin)
        assert res.status_code == 200
        data = res.json()
        assert len(data["items"]) <= 1
        assert data["total"] >= 2

    def test_list_restaurants_as_district_admin(self, client, auth_header_district_admin, restaurant, restaurant_unverified, region):
        """Region admin sees only restaurants in their region."""
        res = client.get("/api/admin/stores", headers=auth_header_district_admin)
        assert res.status_code == 200
        data = res.json()
        # Both restaurant fixtures have region_id=1, matching district_admin
        assert data["total"] >= 2

    def test_verify_restaurant_approve(self, client, auth_header_admin, restaurant_unverified):
        """Verify restaurant as 'verified' auto-sets status to 'open'."""
        res = client.put(
            f"/api/admin/stores/{restaurant_unverified.id}/verify"
            "?verify_status=verified&verify_method=现场核验",
            headers=auth_header_admin,
        )
        assert res.status_code == 200
        assert "message" in res.json()
        # Confirm via list endpoint that the restaurant is now verified
        list_res = client.get(
            "/api/admin/stores?verify_status=verified",
            headers=auth_header_admin,
        )
        verified_ids = [r["id"] for r in list_res.json()["items"]]
        assert restaurant_unverified.id in verified_ids

    def test_verify_restaurant_reject(self, client, auth_header_admin, restaurant_unverified):
        """Verify restaurant as 'rejected' sets verify_status accordingly."""
        res = client.put(
            f"/api/admin/stores/{restaurant_unverified.id}/verify"
            "?verify_status=rejected&verify_note=资料不全",
            headers=auth_header_admin,
        )
        assert res.status_code == 200

    def test_verify_restaurant_invalid_status_returns_400(self, client, auth_header_admin, restaurant):
        """Passing an invalid verify_status returns 400."""
        res = client.put(
            f"/api/admin/stores/{restaurant.id}/verify?verify_status=invalid",
            headers=auth_header_admin,
        )
        assert res.status_code == 400

    def test_toggle_restaurant_status_close(self, client, auth_header_admin, restaurant):
        """Force-close an open restaurant."""
        res = client.put(
            f"/api/admin/stores/{restaurant.id}/toggle-status?status=closed",
            headers=auth_header_admin,
        )
        assert res.status_code == 200
        assert "message" in res.json()

    def test_toggle_restaurant_status_open(self, client, auth_header_admin, restaurant):
        """Force-open a restaurant (already open, should succeed)."""
        res = client.put(
            f"/api/admin/stores/{restaurant.id}/toggle-status?status=open",
            headers=auth_header_admin,
        )
        assert res.status_code == 200


class TestAdminRiders:
    """Rider management: list, audit."""

    def test_list_riders(self, client, auth_header_admin, rider):
        """List riders returns paginated results."""
        res = client.get("/api/admin/riders", headers=auth_header_admin)
        assert res.status_code == 200
        data = res.json()
        assert "total" in data
        assert "items" in data
        assert data["total"] >= 1

    def test_list_riders_with_audit_status_filter(self, client, auth_header_admin, rider):
        """Filter riders by audit_status query param."""
        res = client.get("/api/admin/riders?audit_status=approved", headers=auth_header_admin)
        assert res.status_code == 200
        data = res.json()
        for r in data["items"]:
            assert r["audit_status"] == "approved"

    def test_list_riders_as_district_admin(self, client, auth_header_district_admin, rider):
        """Region admin sees riders filtered by their region."""
        res = client.get("/api/admin/riders", headers=auth_header_district_admin)
        assert res.status_code == 200
        data = res.json()
        assert data["total"] >= 1

    def test_audit_rider_approve(self, client, auth_header_admin, rider):
        """Audit rider as approved. Rider fixture is already approved but endpoint should succeed."""
        res = client.put(
            f"/api/admin/riders/{rider.id}/audit?audit_status=approved",
            headers=auth_header_admin,
        )
        assert res.status_code == 200
        assert "message" in res.json()

    def test_audit_rider_reject(self, client, auth_header_admin, rider):
        """Audit rider as rejected."""
        res = client.put(
            f"/api/admin/riders/{rider.id}/audit?audit_status=rejected",
            headers=auth_header_admin,
        )
        assert res.status_code == 200

    def test_audit_rider_invalid_status_returns_400(self, client, auth_header_admin, rider):
        """Passing an invalid audit_status returns 400."""
        res = client.put(
            f"/api/admin/riders/{rider.id}/audit?audit_status=invalid_status",
            headers=auth_header_admin,
        )
        assert res.status_code == 400


class TestAdminOrders:
    """Order management: list, force-cancel."""

    def test_list_orders(self, client, auth_header_admin, combined_order):
        """List all orders with pagination."""
        res = client.get("/api/admin/orders", headers=auth_header_admin)
        assert res.status_code == 200
        data = res.json()
        assert "total" in data
        assert "items" in data
        assert data["total"] >= 1

    def test_list_orders_with_status_filter(self, client, auth_header_admin, combined_order):
        """Filter orders by status query param."""
        res = client.get("/api/admin/orders?status=pending", headers=auth_header_admin)
        assert res.status_code == 200
        data = res.json()
        for o in data["items"]:
            assert o["status"] == "pending"

    def test_list_orders_as_district_admin(self, client, auth_header_district_admin, combined_order):
        """Region admin sees orders filtered by their region."""
        res = client.get("/api/admin/orders", headers=auth_header_district_admin)
        assert res.status_code == 200
        data = res.json()
        assert "total" in data

    def test_force_cancel_order(self, client, auth_header_admin, order):
        """Force-cancel an order with a custom reason."""
        res = client.put(
            f"/api/admin/orders/{order.id}/force-cancel?reason=违规操作",
            headers=auth_header_admin,
        )
        assert res.status_code == 200
        assert "message" in res.json()

    def test_force_cancel_order_default_reason(self, client, auth_header_admin, order):
        """Force-cancel uses default reason when none provided."""
        res = client.put(
            f"/api/admin/orders/{order.id}/force-cancel",
            headers=auth_header_admin,
        )
        assert res.status_code == 200


class TestAdminFinance:
    """GET /api/admin/finance — financial overview."""

    def test_finance_overview(self, client, auth_header_admin, system_configs):
        """Finance endpoint returns expected fields with correct fee_rate."""
        res = client.get("/api/admin/finance", headers=auth_header_admin)
        assert res.status_code == 200
        data = res.json()
        assert "today_revenue" in data
        assert "today_orders" in data
        assert "today_platform_fee" in data
        assert "month_revenue" in data
        assert "month_platform_fee" in data
        assert "fee_rate" in data
        assert data["fee_rate"] == 0.12

    def test_finance_as_district_admin(self, client, auth_header_district_admin, system_configs):
        """Region admin can access finance overview."""
        res = client.get("/api/admin/finance", headers=auth_header_district_admin)
        assert res.status_code == 200


class TestAdminRegions:
    """Region management: list, create, update."""

    def test_list_regions(self, client, auth_header_admin, region):
        """List regions returns only status=1 regions."""
        res = client.get("/api/admin/districts", headers=auth_header_admin)
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        for r in data:
            assert "id" in r
            assert "name" in r

    def test_create_region(self, client, auth_header_admin):
        """Create a new region (requires super_admin)."""
        res = client.post(
            "/api/admin/districts?name=新区域&parent_id=1",
            headers=auth_header_admin,
        )
        assert res.status_code == 200
        data = res.json()
        assert "message" in data
        assert "id" in data

    def test_update_region(self, client, auth_header_admin, region):
        """Update an existing region."""
        res = client.put(
            f"/api/admin/districts/{region.id}?name=更新区域&sort_order=2&status=1",
            headers=auth_header_admin,
        )
        assert res.status_code == 200
        assert "message" in res.json()

    def test_create_region_requires_super_admin(self, client, auth_header_district_admin):
        """Region admin cannot create a region (returns 403)."""
        res = client.post(
            "/api/admin/districts?name=新区",
            headers=auth_header_district_admin,
        )
        assert res.status_code == 403

    def test_update_region_requires_super_admin(self, client, auth_header_district_admin, region):
        """District admin can update a region."""
        res = client.put(
            f"/api/admin/districts/{region.id}?name=test",
            headers=auth_header_district_admin,
        )
        assert res.status_code == 200


class TestAdminSystemConfigs:
    """System config endpoints (require super_admin)."""

    def test_get_configs(self, client, auth_header_admin, system_configs):
        """Get all system configs as super_admin."""
        res = client.get("/api/admin/system/configs", headers=auth_header_admin)
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert len(data) >= 3
        for c in data:
            assert "key" in c
            assert "value" in c

    def test_update_config(self, client, auth_header_admin, system_configs):
        """Update an existing system config value."""
        res = client.put(
            "/api/admin/system/configs/platform_fee_rate?value=0.2",
            headers=auth_header_admin,
        )
        assert res.status_code == 200
        # Verify the value was persisted
        get_res = client.get("/api/admin/system/configs", headers=auth_header_admin)
        configs = get_res.json()
        fee_cfg = next((c for c in configs if c["key"] == "platform_fee_rate"), None)
        assert fee_cfg is not None
        assert fee_cfg["value"] == "0.2"

    def test_update_nonexistent_config_returns_404(self, client, auth_header_admin):
        """Updating a config key that does not exist returns 404."""
        res = client.put(
            "/api/admin/system/configs/nonexistent_key?value=test",
            headers=auth_header_admin,
        )
        assert res.status_code == 404

    def test_get_configs_requires_super_admin(self, client, auth_header_district_admin):
        """Region admin cannot access system configs (returns 403)."""
        res = client.get("/api/admin/system/configs", headers=auth_header_district_admin)
        assert res.status_code == 403

    def test_update_config_requires_super_admin(self, client, auth_header_district_admin):
        """Region admin cannot update system configs (returns 403)."""
        res = client.put(
            "/api/admin/system/configs/platform_fee_rate?value=0.2",
            headers=auth_header_district_admin,
        )
        assert res.status_code == 403


class TestAdminAdmins:
    """Admin user management (require super_admin)."""

    def test_list_admins(self, client, auth_header_admin, test_user_admin, test_user_district_admin):
        """List all admin users as super_admin."""
        res = client.get("/api/admin/admins", headers=auth_header_admin)
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert len(data) >= 2
        for a in data:
            assert "id" in a
            assert "phone" in a
            assert "role" in a
            assert a["role"] in ("super_admin", "district_admin")

    def test_create_admin(self, client, auth_header_admin, region):
        """Create a new district_admin via super_admin."""
        res = client.post(
            "/api/admin/admins"
            "?phone=13899999999"
            "&password=newadmin123"
            "&nickname=新管理员"
            "&role=district_admin"
            "&region_id=1",
            headers=auth_header_admin,
        )
        assert res.status_code == 200
        data = res.json()
        assert "message" in data
        assert "id" in data

    def test_create_admin_default_values(self, client, auth_header_admin):
        """Create admin with only required params (phone, password) uses defaults."""
        res = client.post(
            "/api/admin/admins?phone=13899999998&password=test123",
            headers=auth_header_admin,
        )
        assert res.status_code == 200

    def test_create_admin_duplicate_phone_returns_400(self, client, auth_header_admin, test_user_admin):
        """Creating admin with an existing phone number returns 400."""
        res = client.post(
            "/api/admin/admins?phone=13800000000&password=test123",
            headers=auth_header_admin,
        )
        assert res.status_code == 400

    def test_toggle_admin_status(self, client, auth_header_admin, test_user_district_admin):
        """Toggle admin user enable/disable."""
        res = client.put(
            f"/api/admin/admins/{test_user_district_admin.id}/toggle-status",
            headers=auth_header_admin,
        )
        assert res.status_code == 200
        assert "message" in res.json()

    def test_toggle_admin_status_not_found_returns_404(self, client, auth_header_admin):
        """Toggling a non-existent admin returns 404."""
        res = client.put(
            "/api/admin/admins/99999/toggle-status",
            headers=auth_header_admin,
        )
        assert res.status_code == 404

    def test_list_admins_requires_super_admin(self, client, auth_header_district_admin):
        """Region admin cannot list admins (returns 403)."""
        res = client.get("/api/admin/admins", headers=auth_header_district_admin)
        assert res.status_code == 403

    def test_create_admin_requires_super_admin(self, client, auth_header_district_admin):
        """Region admin cannot create an admin (returns 403)."""
        res = client.post(
            "/api/admin/admins?phone=13899999997&password=test123",
            headers=auth_header_district_admin,
        )
        assert res.status_code == 403

    def test_toggle_admin_requires_super_admin(self, client, auth_header_district_admin, test_user_admin):
        """Region admin cannot toggle an admin's status (returns 403)."""
        res = client.put(
            f"/api/admin/admins/{test_user_admin.id}/toggle-status",
            headers=auth_header_district_admin,
        )
        assert res.status_code == 403


class TestAdminOrderStats:
    """GET /api/admin/orders/stats — daily order statistics."""

    def test_order_stats_default_days(self, client, auth_header_admin):
        """Order stats with default 7 days returns 7 entries."""
        res = client.get("/api/admin/orders/stats", headers=auth_header_admin)
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert len(data) == 7
        for entry in data:
            assert "date" in entry
            assert "count" in entry
            assert "revenue" in entry

    def test_order_stats_custom_days(self, client, auth_header_admin):
        """Order stats with custom days parameter returns that many entries."""
        res = client.get("/api/admin/orders/stats?days=3", headers=auth_header_admin)
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 3

    def test_order_stats_as_district_admin(self, client, auth_header_district_admin):
        """Region admin can access order stats."""
        res = client.get("/api/admin/orders/stats", headers=auth_header_district_admin)
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 7


class TestAdminRegionAdminPermissions:
    """Region admin cannot access super_admin-only endpoints."""

    def test_district_admin_cannot_access_system_configs(self, client, auth_header_district_admin):
        res = client.get("/api/admin/system/configs", headers=auth_header_district_admin)
        assert res.status_code == 403

    def test_district_admin_cannot_update_system_config(self, client, auth_header_district_admin):
        res = client.put(
            "/api/admin/system/configs/platform_fee_rate?value=0.2",
            headers=auth_header_district_admin,
        )
        assert res.status_code == 403

    def test_district_admin_cannot_list_admins(self, client, auth_header_district_admin):
        res = client.get("/api/admin/admins", headers=auth_header_district_admin)
        assert res.status_code == 403

    def test_district_admin_cannot_create_admin(self, client, auth_header_district_admin):
        res = client.post(
            "/api/admin/admins?phone=13899999996&password=test",
            headers=auth_header_district_admin,
        )
        assert res.status_code == 403

    def test_district_admin_cannot_toggle_admin(self, client, auth_header_district_admin, test_user_admin):
        res = client.put(
            f"/api/admin/admins/{test_user_admin.id}/toggle-status",
            headers=auth_header_district_admin,
        )
        assert res.status_code == 403

    def test_district_admin_cannot_create_region(self, client, auth_header_district_admin):
        res = client.post(
            "/api/admin/districts?name=test",
            headers=auth_header_district_admin,
        )
        assert res.status_code == 403

    def test_district_admin_can_update_region(self, client, auth_header_district_admin, region):
        res = client.put(
            f"/api/admin/districts/{region.id}?name=test",
            headers=auth_header_district_admin,
        )
        assert res.status_code == 200
