import pytest


class TestUserRestaurantList:
    """Tests for GET /api/user/restaurants (list restaurants)."""

    def test_list_restaurants_only_verified_and_open(self, client, restaurant, restaurant_unverified):
        """List should only include restaurants with status='open' and verify_status='verified'."""
        res = client.get("/api/user/restaurants")
        assert res.status_code == 200
        data = res.json()
        assert data["total"] >= 1
        names = [r["name"] for r in data["items"]]
        assert restaurant.name in names
        assert restaurant_unverified.name not in names

    def test_list_restaurants_category_filter(self, client, restaurant):
        """Filter by category should return only matching restaurants."""
        # Filter by the restaurant's category
        res = client.get("/api/user/restaurants", params={"category": restaurant.category})
        assert res.status_code == 200
        data = res.json()
        assert data["total"] >= 1
        for r in data["items"]:
            assert r["category"] == restaurant.category

        # Filter by a category that doesn't match
        res = client.get("/api/user/restaurants", params={"category": "不存在的分类"})
        assert res.status_code == 200
        data = res.json()
        assert data["total"] == 0

    def test_list_restaurants_keyword_filter(self, client, restaurant):
        """Filter by keyword should match restaurant names containing the keyword."""
        # Keyword that matches
        res = client.get("/api/user/restaurants", params={"keyword": "测试"})
        assert res.status_code == 200
        data = res.json()
        assert data["total"] >= 1
        for r in data["items"]:
            assert "测试" in r["name"]

        # Keyword that doesn't match
        res = client.get("/api/user/restaurants", params={"keyword": "不存在的名称"})
        assert res.status_code == 200
        data = res.json()
        assert data["total"] == 0

    def test_list_restaurants_region_id_filter(self, client, restaurant):
        """Filter by region_id should return only restaurants in that region."""
        res = client.get("/api/user/restaurants", params={"region_id": 1})
        assert res.status_code == 200
        data = res.json()
        assert data["total"] >= 1

        # Non-existent region
        res = client.get("/api/user/restaurants", params={"region_id": 999})
        assert res.status_code == 200
        data = res.json()
        assert data["total"] == 0

    def test_list_restaurants_pagination(self, client, restaurant):
        """Pagination with page and page_size should work correctly."""
        # Default pagination
        res = client.get("/api/user/restaurants")
        assert res.status_code == 200
        data = res.json()
        assert "total" in data
        assert "items" in data

        # Custom page_size
        res = client.get("/api/user/restaurants", params={"page": 1, "page_size": 5})
        assert res.status_code == 200
        data = res.json()
        assert len(data["items"]) <= 5

        # Second page should be empty if total <= page_size
        res = client.get("/api/user/restaurants", params={"page": 2, "page_size": 50})
        assert res.status_code == 200
        data = res.json()
        assert len(data["items"]) == 0


class TestUserRestaurantDetail:
    """Tests for GET /api/user/restaurants/{restaurant_id} (get restaurant detail)."""

    def test_get_restaurant_detail_includes_categories_and_items(
        self, client, restaurant, menu_category, menu_items
    ):
        """Detail should include categories and their items."""
        res = client.get(f"/api/user/restaurants/{restaurant.id}")
        assert res.status_code == 200
        data = res.json()
        assert data["id"] == restaurant.id
        assert data["name"] == restaurant.name
        assert data["category"] == restaurant.category
        assert data["delivery_fee"] == restaurant.delivery_fee
        assert data["min_price"] == restaurant.min_price
        assert data["status"] == "open"
        assert data["verify_status"] == "verified"

        # Should have categories
        assert "categories" in data
        assert len(data["categories"]) == 1
        cat = data["categories"][0]
        assert cat["name"] == menu_category.name

        # Should have items inside the category
        assert "items" in cat
        item_names = [item["name"] for item in cat["items"]]
        assert "羊肉串" in item_names
        assert "牛肉串" in item_names
        # Items with status=0 should also appear in detail (they are part of the menu)
        assert "已下架菜品" in item_names

    def test_get_restaurant_not_found_returns_404(self, client):
        """Requesting a non-existent restaurant should return 404."""
        res = client.get("/api/user/restaurants/99999")
        assert res.status_code == 404
        assert res.json()["detail"] == "餐厅不存在"

    def test_unverified_restaurant_detail_is_accessible(self, client, restaurant_unverified):
        """Detail of an unverified restaurant should still be directly accessible by ID."""
        res = client.get(f"/api/user/restaurants/{restaurant_unverified.id}")
        assert res.status_code == 200
        data = res.json()
        assert data["id"] == restaurant_unverified.id
        assert data["name"] == restaurant_unverified.name
        assert data["verify_status"] == "unverified"
