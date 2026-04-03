"""
Shared fixtures for the entire test suite.
All test files import from here automatically via pytest's conftest discovery.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import get_db
from app.models import Base

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_suite.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Isolated DB per test — created fresh, dropped after."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db):
    """TestClient wired to the test DB session."""
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()


# ── Reusable helpers ─────────────────────────────────────────────

def register_and_login(client, email="user@test.com", password="pass123456"):
    """Register + login. Returns the client (cookies set automatically)."""
    client.post("/api/auth/register", json={"email": email, "password": password})
    client.post("/api/auth/login",    json={"email": email, "password": password})
    return client


def create_product(client, **overrides):
    """POST /api/products/ with sensible defaults."""
    payload = {
        "external_id": "ext-001",
        "source":       "grailed",
        "name":         "Test Jacket",
        "url":          "https://grailed.com/001",
        "category":     "Jackets",
        "description":  "A test jacket",
        "current_price": 299.99,
        "currency":     "USD",
        **overrides,
    }
    return client.post("/api/products/", json=payload)
