"""
Tests for the analytics overview endpoint:
  GET /api/products/analytics/overview
"""

from tests.conftest import register_and_login, create_product


class TestAnalyticsOverview:

    def test_empty_when_no_products(self, client):
        """Fresh account with no products returns all-zero stats."""
        register_and_login(client)
        resp = client.get("/api/products/analytics/overview")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_products"] == 0
        assert data["products_by_source"] == {}

    def test_requires_authentication(self, client):
        """Analytics endpoint is protected — no session → 401."""
        resp = client.get("/api/products/analytics/overview")
        assert resp.status_code == 401

    def test_counts_only_own_products(self, client):
        """
        analytics/overview is user-scoped.
        User B's stats must not include User A's products.
        """
        # User A adds 2 products
        register_and_login(client, email="a@test.com")
        create_product(client, external_id="a1", source="grailed",      category="Jackets", current_price=300)
        create_product(client, external_id="a2", source="fashionphile", category="Bags",    current_price=800)

        # User B adds 1 product
        client.post("/api/auth/logout")
        register_and_login(client, email="b@test.com")
        create_product(client, external_id="b1", source="1stdibs", category="Watches", current_price=10000)

        # User B sees only their own data
        resp = client.get("/api/products/analytics/overview")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_products"] == 1
        assert "1stdibs" in data["products_by_source"]
        assert "grailed" not in data["products_by_source"]

    def test_source_count_is_accurate(self, client):
        """products_by_source reflects the exact count per marketplace."""
        register_and_login(client)
        create_product(client, external_id="g1", source="grailed")
        create_product(client, external_id="g2", source="grailed",      name="Product 2")
        create_product(client, external_id="f1", source="fashionphile", name="Product 3")

        data = client.get("/api/products/analytics/overview").json()
        assert data["products_by_source"]["grailed"] == 2
        assert data["products_by_source"]["fashionphile"] == 1

    def test_avg_price_by_category_is_correct(self, client):
        """Average price calculation is mathematically correct per category."""
        register_and_login(client)
        create_product(client, external_id="j1", category="Jackets", current_price=200)
        create_product(client, external_id="j2", category="Jackets", current_price=400, source="fashionphile")

        data = client.get("/api/products/analytics/overview").json()
        jackets = data["avg_price_by_category"].get("Jackets")
        assert jackets is not None
        assert jackets["average"] == 300.0
        assert jackets["count"] == 2
