"""
Test suite for the Product Price Monitoring System
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import get_db
from app.models import Base, User, Product, Source, PriceHistory, PriceChangeEvent
from app.utils.auth import get_password_hash, verify_password
from datetime import datetime

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Create test database and tables"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db):
    """Create test client"""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


@pytest.fixture
def test_user(db):
    """Create a test user"""
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("password123"),
        api_key="test-api-key"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ============ Authentication Tests ============

def test_user_registration(client):
    """Test user registration"""
    response = client.post(
        "/api/auth/register",
        json={"email": "newuser@example.com", "password": "securepass123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "newuser@example.com"


def test_user_registration_duplicate_email(client, test_user):
    """Test registration fails with duplicate email"""
    response = client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "password123"}
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


def test_user_login(client, test_user):
    """Test user login"""
    response = client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_user_login_invalid_password(client, test_user):
    """Test login fails with incorrect password"""
    response = client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401


# ============ Product Tests ============

def test_create_product(client, test_user, db):
    """Test creating a product"""
    response = client.post(
        "/api/products/",
        json={
            "external_id": "grailed-123",
            "source": "grailed",
            "name": "Designer Jacket",
            "url": "https://grailed.com/123",
            "category": "Jackets",
            "description": "Premium designer jacket",
            "current_price": 299.99,
            "currency": "USD"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Designer Jacket"
    assert data["current_price"] == 299.99


def test_create_duplicate_product(client, test_user, db):
    """Test creating a duplicate product fails"""
    # Create first product
    client.post(
        "/api/products/",
        json={
            "external_id": "grailed-123",
            "source": "grailed",
            "name": "Designer Jacket",
            "current_price": 299.99,
        }
    )

    # Try to create duplicate
    response = client.post(
        "/api/products/",
        json={
            "external_id": "grailed-123",
            "source": "grailed",
            "name": "Designer Jacket 2",
            "current_price": 250.00,
        }
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_list_products(client, test_user, db):
    """Test listing products"""
    # Create some products
    for i in range(3):
        client.post(
            "/api/products/",
            json={
                "external_id": f"product-{i}",
                "source": "grailed",
                "name": f"Product {i}",
                "current_price": 100 + (i * 50),
            }
        )

    response = client.get("/api/products/?skip=0&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3


def test_filter_by_price_range(client, test_user, db):
    """Test filtering products by price range"""
    # Create products with different prices
    for price in [100, 200, 300, 400]:
        client.post(
            "/api/products/",
            json={
                "external_id": f"product-{price}",
                "source": "grailed",
                "name": f"Product {price}",
                "current_price": price,
            }
        )

    # Filter by price range
    response = client.get("/api/products/?skip=0&limit=10&min_price=200&max_price=350")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2  # 200 and 300


def test_filter_by_category(client, test_user, db):
    """Test filtering products by category"""
    categories = ["Jackets", "Pants", "Shirts"]
    for i, cat in enumerate(categories):
        client.post(
            "/api/products/",
            json={
                "external_id": f"product-{i}",
                "source": "grailed",
                "name": f"Product {i}",
                "category": cat,
                "current_price": 100,
            }
        )

    response = client.get("/api/products/?skip=0&limit=10&category=Jackets")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1


def test_get_product_detail(client, test_user, db):
    """Test getting product details with price history"""
    # Create product
    create_response = client.post(
        "/api/products/",
        json={
            "external_id": "grailed-123",
            "source": "grailed",
            "name": "Designer Jacket",
            "current_price": 299.99,
        }
    )
    product_id = create_response.json()["id"]

    # Get product details
    response = client.get(f"/api/products/{product_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Designer Jacket"
    assert len(data["price_history"]) >= 1


def test_product_not_found(client, test_user, db):
    """Test getting non-existent product"""
    response = client.get("/api/products/9999")
    assert response.status_code == 404


# ============ Price History & Analytics Tests ============

def test_get_analytics_overview(client, test_user, db):
    """Test getting analytics overview"""
    # Create some products
    for i in range(3):
        client.post(
            "/api/products/",
            json={
                "external_id": f"product-{i}",
                "source": "grailed",
                "name": f"Product {i}",
                "category": "Jackets" if i % 2 == 0 else "Pants",
                "current_price": 100 + (i * 50),
            }
        )

    response = client.get("/api/products/analytics/overview")
    assert response.status_code == 200
    data = response.json()
    assert data["total_products"] == 3
    assert "grailed" in data["products_by_source"]


# ============ Edge Cases & Error Handling ============

def test_pagination(client, test_user, db):
    """Test pagination"""
    # Create 25 products
    for i in range(25):
        client.post(
            "/api/products/",
            json={
                "external_id": f"product-{i:03d}",
                "source": "grailed",
                "name": f"Product {i}",
                "current_price": 100 + i,
            }
        )

    # Test page 1
    response = client.get("/api/products/?skip=0&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 10
    assert data["total"] == 25
    assert data["total_pages"] == 3

    # Test page 2
    response = client.get("/api/products/?skip=10&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 10


def test_invalid_price_in_filter(client, test_user, db):
    """Test invalid price filter"""
    response = client.get("/api/products/?skip=0&limit=10&min_price=-100")
    # Should fail validation
    assert response.status_code == 422


def test_invalid_source_filter(client, test_user, db):
    """Test invalid source filter"""
    response = client.get("/api/products/?skip=0&limit=10&source=invalid_source")
    assert response.status_code == 400
    assert "Invalid source" in response.json()["detail"]
