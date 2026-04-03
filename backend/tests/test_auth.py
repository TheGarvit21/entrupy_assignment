"""
Tests for /api/auth/* endpoints:
  POST /register
  POST /login
  POST /logout
  GET  /me
"""

from tests.conftest import register_and_login


class TestRegister:

    def test_success(self, client):
        """New user registers successfully."""
        resp = client.post("/api/auth/register", json={
            "email": "new@example.com", "password": "strongpass1"
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["email"] == "new@example.com"
        assert "id" in body

    def test_duplicate_email_rejected(self, client):
        """Second registration with the same email returns 400."""
        client.post("/api/auth/register", json={"email": "dup@test.com", "password": "pass1"})
        resp = client.post("/api/auth/register", json={"email": "dup@test.com", "password": "pass2"})
        assert resp.status_code == 400
        assert "already registered" in resp.json()["detail"]

    def test_short_password_accepted(self, client):
        """
        Schema does not currently enforce a minimum password length.
        This test documents the existing behavior.
        To enforce length, add `Field(min_length=8)` to UserCreate.password.
        """
        resp = client.post("/api/auth/register", json={"email": "a@b.com", "password": "12"})
        assert resp.status_code == 200


class TestLogin:

    def test_success_sets_cookie(self, client):
        """Valid credentials set an HttpOnly access_token cookie."""
        client.post("/api/auth/register", json={"email": "u@e.com", "password": "pass123"})
        resp = client.post("/api/auth/login",    json={"email": "u@e.com", "password": "pass123"})
        assert resp.status_code == 200
        assert "access_token" in resp.cookies

    def test_wrong_password_rejected(self, client):
        """Incorrect password returns 401."""
        client.post("/api/auth/register", json={"email": "u@e.com", "password": "correct"})
        resp = client.post("/api/auth/login",    json={"email": "u@e.com", "password": "wrong"})
        assert resp.status_code == 401

    def test_unknown_email_rejected(self, client):
        """Login attempt with unregistered email returns 401."""
        resp = client.post("/api/auth/login", json={"email": "ghost@test.com", "password": "any"})
        assert resp.status_code == 401


class TestGetMe:

    def test_returns_user_when_authenticated(self, client):
        """/auth/me returns the current user's profile."""
        register_and_login(client)
        resp = client.get("/api/auth/me")
        assert resp.status_code == 200
        assert resp.json()["email"] == "user@test.com"

    def test_401_when_unauthenticated(self, client):
        """/auth/me requires an active session."""
        resp = client.get("/api/auth/me")
        assert resp.status_code == 401


class TestLogout:

    def test_clears_session(self, client):
        """After logout, /auth/me returns 401."""
        register_and_login(client)
        client.post("/api/auth/logout")
        resp = client.get("/api/auth/me")
        assert resp.status_code == 401
