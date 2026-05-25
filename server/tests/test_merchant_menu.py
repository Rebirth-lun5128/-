import pytest


class TestMenuCategory:
    """Tests for /api/merchant/menu/categories endpoints"""

    def test_list_categories(self, client, auth_header_merchant, restaurant, menu_category):
        """List categories returns the pre-created category."""
        res = client.get("/api/merchant/menu/categories", headers=auth_header_merchant)
        assert res.status_code == 200
        categories = res.json()
        assert len(categories) >= 1
        ids = [c["id"] for c in categories]
        assert menu_category.id in ids

    def test_create_category(self, client, auth_header_merchant, restaurant):
        """Create a new category."""
        res = client.post(
            "/api/merchant/menu/categories",
            json={"name": "新品", "sort_order": 1},
            headers=auth_header_merchant,
        )
        assert res.status_code == 200
        assert res.json()["name"] == "新品"

    def test_delete_category(self, client, auth_header_merchant, restaurant):
        """Delete an existing category and verify it is removed from list."""
        create = client.post(
            "/api/merchant/menu/categories",
            json={"name": "待删除"},
            headers=auth_header_merchant,
        )
        cat_id = create.json()["id"]

        res = client.delete(
            f"/api/merchant/menu/categories/{cat_id}", headers=auth_header_merchant
        )
        assert res.status_code == 200

        # Verify it is gone from the list
        list_res = client.get("/api/merchant/menu/categories", headers=auth_header_merchant)
        ids = [c["id"] for c in list_res.json()]
        assert cat_id not in ids

    def test_delete_nonexistent_category(self, client, auth_header_merchant, restaurant):
        """Delete a non-existent category returns 404."""
        res = client.delete(
            "/api/merchant/menu/categories/99999", headers=auth_header_merchant
        )
        assert res.status_code == 404


class TestMenuItem:
    """Tests for /api/merchant/menu/items endpoints"""

    def test_list_items(self, client, auth_header_merchant, restaurant, menu_items):
        """List items returns the pre-created items."""
        res = client.get("/api/merchant/menu/items", headers=auth_header_merchant)
        assert res.status_code == 200
        items = res.json()
        assert len(items) >= 3

    def test_list_items_filtered_by_category(self, client, auth_header_merchant, restaurant, menu_category, menu_items):
        """List items filtered by category_id returns only items in that category."""
        res = client.get(
            f"/api/merchant/menu/items?category_id={menu_category.id}",
            headers=auth_header_merchant,
        )
        assert res.status_code == 200
        items = res.json()
        for item in items:
            assert item["category_id"] == menu_category.id

    def test_create_item(self, client, auth_header_merchant, restaurant, menu_category):
        """Create a new menu item."""
        body = {
            "category_id": menu_category.id,
            "name": "炒饭",
            "price": 12,
            "description": "招牌炒饭",
            "image": "/img/1.png",
        }
        res = client.post("/api/merchant/menu/items", json=body, headers=auth_header_merchant)
        assert res.status_code == 200
        data = res.json()
        assert data["name"] == "炒饭"
        assert float(data["price"]) == 12

    def test_update_item(self, client, auth_header_merchant, restaurant, menu_items):
        """Update an item's name and price."""
        item1 = menu_items[0]
        res = client.put(
            f"/api/merchant/menu/items/{item1.id}",
            json={"name": "大串烤串", "price": 20},
            headers=auth_header_merchant,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["name"] == "大串烤串"
        assert float(data["price"]) == 20

    def test_toggle_item_status(self, client, auth_header_merchant, restaurant, menu_items):
        """Toggle item status from enabled to disabled and back."""
        item1 = menu_items[0]

        # Disable
        res = client.put(
            f"/api/merchant/menu/items/{item1.id}/status?status=0",
            headers=auth_header_merchant,
        )
        assert res.status_code == 200
        assert int(res.json()["status"]) == 0

        # Enable
        res2 = client.put(
            f"/api/merchant/menu/items/{item1.id}/status?status=1",
            headers=auth_header_merchant,
        )
        assert res2.status_code == 200
        assert int(res2.json()["status"]) == 1

    def test_delete_item(self, client, auth_header_merchant, restaurant, menu_category):
        """Delete a newly created item."""
        create = client.post(
            "/api/merchant/menu/items",
            json={"category_id": menu_category.id, "name": "临时菜", "price": 5},
            headers=auth_header_merchant,
        )
        item_id = create.json()["id"]

        res = client.delete(
            f"/api/merchant/menu/items/{item_id}", headers=auth_header_merchant
        )
        assert res.status_code == 200
