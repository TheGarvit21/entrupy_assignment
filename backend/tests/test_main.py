"""
Full test suite for Product Price Monitoring System
Covers: Auth, Products (user-scoped), Analytics, Edge Cases
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import get_db
from app.models import Base, User, Product, Source, PriceHistory
from app.utils.auth import get_password_hash, generate_api_key

# ──────────────────────────────────────────────
# In-memory SQLite for tests (isolated per run)
# ──────────────────────────────────────────────
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_suite.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ──────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────

@pytest.fixture(scope="function")
def db():
    """Fresh DB for every test function."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db):
    """TestClient wired to the test DB."""
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()


def _register_and_login(client, email="user@test.com", password="pass123456"):
    """Helper: register + login → returns authenticated client session."""
    client.post("/api/auth/register", json={"email": email, "password": password})
    client.post("/api/auth/login",    json={"email": email, "password": password})
    return client


def _create_product(client, **overrides):
    """Helper: create a product with defaults."""
    payload = {
        "external_id": "ext-001",
        "source": "grailed",
        "name": "Test Jacket",
        "url": "https://grailed.com/001",
        "category": "Jackets",
        "description": "A test jacket",
        "current_price": 299.99,
        "currency": "USD",
        **overrides
    }
    return client.post("/api/products/", json=payload)


# ══════════════════════════════════════════════
# AUTH TESTS
# ══════════════════════════════════════════════

class TestAuth:

    def test_register_success(self, client):
        """Register a new user."""
        resp = client.post("/api/auth/register", json={
            "email": "new@example.com", "password": "strongpass1"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "new@example.com"
        assert "id" in data

    def test_register_duplicate_email(self, client):
        """Second registration with same email → 400."""
        client.post("/api/auth/register", json={"email": "dup@test.com", "password": "pass1"})
        resp = client.post("/api/auth/register", json={"email": "dup@test.com", "password": "pass2"})
        assert resp.status_code == 400
        assert "already registered" in resp.json()["detail"]

    def test_register_short_password(self, client):
        """
        Currently the schema accepts any-length passwords (no min_length set).
        This test documents the current behavior. Add Field(min_length=8) to
        UserCreate.password in schemas.py to enforce a minimum.
        """
        resp = client.post("/api/auth/register", json={"email": "a@b.com", "password": "12"})
        # No min-length enforced yet — registration succeeds
        assert resp.status_code == 200

    def test_login_success(self, client):
        """Valid credentials return a cookie."""
        client.post("/api/auth/register", json={"email": "u@e.com", "password": "pass123"})
        resp = client.post("/api/auth/login", json={"email": "u@e.com", "password": "pass123"})
        assert resp.status_code == 200
        assert "access_token" in resp.cookies

    def test_login_wrong_password(self, client):
        """Wrong password → 401."""
        client.post("/api/auth/register", json={"email": "u@e.com", "password": "correct"})
        resp = client.post("/api/auth/login", json={"email": "u@e.com", "password": "wrong"})
        assert resp.status_code == 401

    def test_login_unregistered_email(self, client):
        """Login with unknown email → 401."""
        resp = client.post("/api/auth/login", json={"email": "ghost@test.com", "password": "any"})
        assert resp.status_code == 401

    def test_get_me_authenticated(self, client):
        """/auth/me returns user info when logged in."""
        _register_and_login(client)
        resp = client.get("/api/auth/me")
        assert resp.status_code == 200
        assert resp.json()["email"] == "user@test.com"

    def test_get_me_unauthenticated(self, client):
        """/auth/me requires authentication."""
        resp = client.get("/api/auth/me")
        assert resp.status_code == 401

    def test_logout_clears_session(self, client):
        """After logout /auth/me should return 401."""
        _register_and_login(client)
        client.post("/api/auth/logout")
        resp = client.get("/api/auth/me")
        assert resp.status_code == 401


# ══════════════════════════════════════════════
# PRODUCT CRUD TESTS
# ══════════════════════════════════════════════

class TestProductCRUD:

    def test_create_product_authenticated(self, client):
        """Authenticated user can create a product."""
        _register_and_login(client)
        resp = _create_product(client)
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Test Jacket"
        assert data["current_price"] == 299.99
        assert data["source"] == "grailed"

    def test_create_product_unauthenticated(self, client):
        """Unauthenticated request → 401."""
        resp = _create_product(client)
        assert resp.status_code == 401

    def test_create_duplicate_product_same_user(self, client):
        """Same user cannot add the same external_id+source twice."""
        _register_and_login(client)
        _create_product(client)
        resp = _create_product(client)   # duplicate
        assert resp.status_code == 400
        assert "already track" in resp.json()["detail"]

    def test_create_same_product_different_users(self, client):
        """Two different users CAN track the same product independently."""
        # User A
        _register_and_login(client, email="a@test.com")
        resp_a = _create_product(client, external_id="shared-001")
        assert resp_a.status_code == 200

        # User B (new session)
        client.post("/api/auth/logout")
        _register_and_login(client, email="b@test.com")
        resp_b = _create_product(client, external_id="shared-001")
        assert resp_b.status_code == 200   # no conflict

    def test_list_products_returns_only_own(self, client):
        """User A's list should not contain User B's products."""
        # User A adds 2
        _register_and_login(client, email="a@test.com")
        _create_product(client, external_id="a-1", name="Product A1")
        _create_product(client, external_id="a-2", name="Product A2")

        # User B adds 1
        client.post("/api/auth/logout")
        _register_and_login(client, email="b@test.com")
        _create_product(client, external_id="b-1", name="Product B1")

        resp = client.get("/api/products/?skip=0&limit=20")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "Product B1"

    def test_list_products_unauthenticated(self, client):
        """List endpoint requires auth."""
        resp = client.get("/api/products/")
        assert resp.status_code == 401

    def test_get_product_detail(self, client):
        """Get a product that belongs to the current user."""
        _register_and_login(client)
        create_resp = _create_product(client)
        pid = create_resp.json()["id"]

        resp = client.get(f"/api/products/{pid}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Test Jacket"
        assert isinstance(data["price_history"], list)
        assert len(data["price_history"]) >= 1   # initial price recorded

    def test_get_product_not_found(self, client):
        """Non-existent product → 404."""
        _register_and_login(client)
        resp = client.get("/api/products/999999")
        assert resp.status_code == 404

    def test_get_other_users_product(self, client):
        """User B cannot access User A's product by ID."""
        _register_and_login(client, email="a@test.com")
        pid = _create_product(client, external_id="private-001").json()["id"]

        client.post("/api/auth/logout")
        _register_and_login(client, email="b@test.com")

        resp = client.get(f"/api/products/{pid}")
        assert resp.status_code == 404   # looks like it doesn't exist to user B

    def test_delete_own_product(self, client):
        """User can delete their own product."""
        _register_and_login(client)
        pid = _create_product(client).json()["id"]

        resp = client.delete(f"/api/products/{pid}")
        assert resp.status_code == 200

        # Confirm gone
        resp2 = client.get(f"/api/products/{pid}")
        assert resp2.status_code == 404

    def test_delete_other_users_product(self, client):
        """User B cannot delete User A's product."""
        _register_and_login(client, email="a@test.com")
        pid = _create_product(client, external_id="a-prod").json()["id"]

        client.post("/api/auth/logout")
        _register_and_login(client, email="b@test.com")

        resp = client.delete(f"/api/products/{pid}")
        assert resp.status_code == 404


# ══════════════════════════════════════════════
# FILTER & PAGINATION TESTS
# ══════════════════════════════════════════════

class TestFiltersAndPagination:

    def _seed_products(self, client):
        """Create 4 test products across different sources/categories."""
        products = [
            {"external_id": "g1", "source": "grailed",      "name": "Jacket A", "category": "Jackets", "current_price": 100},
            {"external_id": "f1", "source": "fashionphile", "name": "Bag A",    "category": "Bags",    "current_price": 500},
            {"external_id": "d1", "source": "1stdibs",      "name": "Watch A",  "category": "Watches", "current_price": 5000},
            {"external_id": "g2", "source": "grailed",      "name": "Jacket B", "category": "Jackets", "current_price": 200},
        ]
        for p in products:
            _create_product(client, **p)

    def test_filter_by_source(self, client):
        _register_and_login(client)
        self._seed_products(client)

        resp = client.get("/api/products/?source=grailed&skip=0&limit=20")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert all(p["source"] == "grailed" for p in data["items"])

    def test_filter_by_category(self, client):
        _register_and_login(client)
        self._seed_products(client)

        resp = client.get("/api/products/?category=Watches&skip=0&limit=20")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_filter_by_price_range(self, client):
        _register_and_login(client)
        self._seed_products(client)

        resp = client.get("/api/products/?min_price=150&max_price=600&skip=0&limit=20")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2   # 200 and 500

    def test_pagination_limit(self, client):
        _register_and_login(client)
        for i in range(15):
            _create_product(client, external_id=f"page-{i:03d}", name=f"Product {i}")

        resp = client.get("/api/products/?skip=0&limit=5")
        data = resp.json()
        assert len(data["items"]) == 5
        assert data["total"] == 15
        assert data["total_pages"] == 3

    def test_pagination_second_page(self, client):
        _register_and_login(client)
        for i in range(15):
            _create_product(client, external_id=f"page-{i:03d}", name=f"Product {i}")

        resp = client.get("/api/products/?skip=5&limit=5")
        assert len(resp.json()["items"]) == 5

    def test_invalid_source_filter(self, client):
        """Unknown source name → 400."""
        _register_and_login(client)
        resp = client.get("/api/products/?source=fakemarket&skip=0&limit=10")
        assert resp.status_code == 400
        assert "Invalid source" in resp.json()["detail"]

    def test_negative_price_filter(self, client):
        """Negative min_price → 422 from FastAPI validation."""
        _register_and_login(client)
        resp = client.get("/api/products/?min_price=-1&skip=0&limit=10")
        assert resp.status_code == 422


# ══════════════════════════════════════════════
# ANALYTICS TESTS
# ══════════════════════════════════════════════

class TestAnalytics:

    def test_analytics_overview_empty(self, client):
        """Analytics with no products returns zeros."""
        _register_and_login(client)
        resp = client.get("/api/products/analytics/overview")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_products"] == 0
        assert data["products_by_source"] == {}

    def test_analytics_counts_user_products(self, client):
        """Analytics only counts the logged-in user's products."""
        _register_and_login(client, email="a@test.com")
        _create_product(client, external_id="a1", source="grailed",      category="Jackets", current_price=300)
        _create_product(client, external_id="a2", source="fashionphile", category="Bags",    current_price=800)

        # user B adds their own
        client.post("/api/auth/logout")
        _register_and_login(client, email="b@test.com")
        _create_product(client, external_id="b1", source="1stdibs", category="Watches", current_price=10000)

        # B checks analytics  → should only see their 1 product
        resp = client.get("/api/products/analytics/overview")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_products"] == 1
        assert "1stdibs" in data["products_by_source"]
        assert "grailed" not in data["products_by_source"]

    def test_analytics_avg_price_by_category(self, client):
        """Average price calculation is correct per category."""
        _register_and_login(client)
        _create_product(client, external_id="j1", category="Jackets", current_price=200)
        _create_product(client, external_id="j2", category="Jackets", current_price=400, source="fashionphile")

        resp = client.get("/api/products/analytics/overview")
        data = resp.json()
        jackets = data["avg_price_by_category"].get("Jackets")
        assert jackets is not None
        assert jackets["average"] == 300.0
        assert jackets["count"] == 2

    def test_analytics_requires_auth(self, client):
        """Analytics endpoint requires authentication."""
        resp = client.get("/api/products/analytics/overview")
        assert resp.status_code == 401


# ══════════════════════════════════════════════
# PRICE HISTORY TESTS
# ══════════════════════════════════════════════

class TestPriceHistory:

    def test_initial_price_recorded(self, client):
        """Creating a product automatically records its first price."""
        _register_and_login(client)
        create_resp = _create_product(client, current_price=500.0)
        pid = create_resp.json()["id"]

        detail = client.get(f"/api/products/{pid}").json()
        assert len(detail["price_history"]) == 1
        assert detail["price_history"][0]["price"] == 500.0

    def test_password_hash_is_secure(self, client):
        """Ensure passwords are never stored in plain text."""
        from app.utils.auth import get_password_hash, verify_password
        raw = "mysecretpassword"
        hashed = get_password_hash(raw)
        assert hashed != raw
        assert verify_password(raw, hashed)
        assert not verify_password("wrongpass", hashed)
