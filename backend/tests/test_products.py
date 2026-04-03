"""
Tests for core product CRUD endpoints:
  POST   /api/products/
  GET    /api/products/
  GET    /api/products/{id}
  DELETE /api/products/{id}
"""

from tests.conftest import register_and_login, create_product


class TestCreateProduct:

    def test_authenticated_user_can_create(self, client):
        """Logged-in user successfully creates a product."""
        register_and_login(client)
        resp = create_product(client)
        assert resp.status_code == 200
        body = resp.json()
        assert body["name"] == "Test Jacket"
        assert body["current_price"] == 299.99
        assert body["source"] == "grailed"

    def test_unauthenticated_request_rejected(self, client):
        """No session cookie → 401 on create."""
        resp = create_product(client)
        assert resp.status_code == 401

    def test_duplicate_by_same_user_rejected(self, client):
        """Same user cannot add the same external_id + source twice."""
        register_and_login(client)
        create_product(client)
        resp = create_product(client)   # identical payload
        assert resp.status_code == 400
        assert "already track" in resp.json()["detail"]

    def test_two_users_can_track_same_product(self, client):
        """
        Different users CAN track the same marketplace product independently.
        Duplicate check is scoped per user, not globally.
        """
        register_and_login(client, email="a@test.com")
        assert create_product(client, external_id="shared-001").status_code == 200

        client.post("/api/auth/logout")
        register_and_login(client, email="b@test.com")
        assert create_product(client, external_id="shared-001").status_code == 200


class TestListProducts:

    def test_returns_only_own_products(self, client):
        """
        User B's list must never include User A's products.
        Core user-isolation guarantee.
        """
        # User A adds 2 products
        register_and_login(client, email="a@test.com")
        create_product(client, external_id="a-1", name="Product A1")
        create_product(client, external_id="a-2", name="Product A2")

        # User B adds 1 product
        client.post("/api/auth/logout")
        register_and_login(client, email="b@test.com")
        create_product(client, external_id="b-1", name="Product B1")

        resp = client.get("/api/products/?skip=0&limit=20")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "Product B1"

    def test_unauthenticated_request_rejected(self, client):
        """List endpoint requires an active session."""
        resp = client.get("/api/products/")
        assert resp.status_code == 401


class TestGetProductDetail:

    def test_returns_product_with_price_history(self, client):
        """Fetching a product includes its initial price history entry."""
        register_and_login(client)
        pid = create_product(client).json()["id"]

        resp = client.get(f"/api/products/{pid}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["name"] == "Test Jacket"
        assert isinstance(body["price_history"], list)
        assert len(body["price_history"]) >= 1

    def test_nonexistent_product_returns_404(self, client):
        """Requesting an ID that doesn't exist → 404."""
        register_and_login(client)
        assert client.get("/api/products/999999").status_code == 404

    def test_cannot_access_other_users_product(self, client):
        """
        User B requesting User A's product ID receives 404, not 403.
        This prevents leaking the existence of other users' data.
        """
        register_and_login(client, email="a@test.com")
        pid = create_product(client, external_id="private-001").json()["id"]

        client.post("/api/auth/logout")
        register_and_login(client, email="b@test.com")
        assert client.get(f"/api/products/{pid}").status_code == 404


class TestDeleteProduct:

    def test_owner_can_delete(self, client):
        """User successfully deletes their own product."""
        register_and_login(client)
        pid = create_product(client).json()["id"]

        assert client.delete(f"/api/products/{pid}").status_code == 200
        assert client.get(f"/api/products/{pid}").status_code == 404   # confirmed gone

    def test_cannot_delete_other_users_product(self, client):
        """User B attempting to delete User A's product → 404."""
        register_and_login(client, email="a@test.com")
        pid = create_product(client, external_id="a-prod").json()["id"]

        client.post("/api/auth/logout")
        register_and_login(client, email="b@test.com")
        assert client.delete(f"/api/products/{pid}").status_code == 404
