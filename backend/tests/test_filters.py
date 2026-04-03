"""
Tests for product filtering and pagination:
  GET /api/products/?source=...
  GET /api/products/?category=...
  GET /api/products/?min_price=...&max_price=...
  GET /api/products/?skip=...&limit=...
"""

import pytest
from tests.conftest import register_and_login, create_product


@pytest.fixture
def seeded_client(client):
    """
    Authenticated client pre-loaded with 4 products across
    different sources, categories, and price points.
    """
    register_and_login(client)
    create_product(client, external_id="g1", source="grailed",      name="Jacket A", category="Jackets", current_price=100)
    create_product(client, external_id="f1", source="fashionphile", name="Bag A",    category="Bags",    current_price=500)
    create_product(client, external_id="d1", source="1stdibs",      name="Watch A",  category="Watches", current_price=5000)
    create_product(client, external_id="g2", source="grailed",      name="Jacket B", category="Jackets", current_price=200)
    return client


class TestSourceFilter:

    def test_filters_by_source(self, seeded_client):
        """Only products from the specified source are returned."""
        resp = seeded_client.get("/api/products/?source=grailed&skip=0&limit=20")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert all(p["source"] == "grailed" for p in data["items"])

    def test_invalid_source_returns_400(self, seeded_client):
        """Unknown marketplace name → 400 with a clear error message."""
        resp = seeded_client.get("/api/products/?source=fakemarket&skip=0&limit=10")
        assert resp.status_code == 400
        assert "Invalid source" in resp.json()["detail"]


class TestCategoryFilter:

    def test_filters_by_category(self, seeded_client):
        """Only products in the specified category are returned."""
        resp = seeded_client.get("/api/products/?category=Watches&skip=0&limit=20")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1


class TestPriceRangeFilter:

    def test_filters_within_range(self, seeded_client):
        """Products outside [min_price, max_price] are excluded."""
        resp = seeded_client.get("/api/products/?min_price=150&max_price=600&skip=0&limit=20")
        assert resp.status_code == 200
        assert resp.json()["total"] == 2   # 200 and 500

    def test_negative_min_price_returns_422(self, client):
        """FastAPI query param validation rejects negative min_price."""
        register_and_login(client)
        resp = client.get("/api/products/?min_price=-1&skip=0&limit=10")
        assert resp.status_code == 422


class TestPagination:

    @pytest.fixture
    def paginated_client(self, client):
        """Authenticated client with 15 products for pagination tests."""
        register_and_login(client)
        for i in range(15):
            create_product(client, external_id=f"page-{i:03d}", name=f"Product {i}")
        return client

    def test_limit_respected(self, paginated_client):
        """Response contains at most `limit` items."""
        resp = paginated_client.get("/api/products/?skip=0&limit=5")
        data = resp.json()
        assert len(data["items"]) == 5
        assert data["total"] == 15
        assert data["total_pages"] == 3

    def test_skip_offsets_results(self, paginated_client):
        """skip=5 returns the second page of results."""
        resp = paginated_client.get("/api/products/?skip=5&limit=5")
        assert len(resp.json()["items"]) == 5

    def test_last_page_returns_remainder(self, paginated_client):
        """Final page returns however many items remain."""
        resp = paginated_client.get("/api/products/?skip=10&limit=5")
        assert len(resp.json()["items"]) == 5
