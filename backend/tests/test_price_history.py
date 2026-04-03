"""
Tests for price history and security utilities:
  - Initial price auto-recorded on product creation
  - Password hashing (bcrypt)
"""

from tests.conftest import register_and_login, create_product


class TestPriceHistory:

    def test_initial_price_recorded_on_create(self, client):
        """
        When a product is created, its current_price is automatically
        written as the first entry in price_history.
        """
        register_and_login(client)
        pid = create_product(client, current_price=500.0).json()["id"]

        detail = client.get(f"/api/products/{pid}").json()
        assert len(detail["price_history"]) == 1
        assert detail["price_history"][0]["price"] == 500.0


class TestPasswordSecurity:

    def test_password_is_hashed_not_stored_plain(self):
        """Plaintext password must never appear in the hashed value."""
        from app.utils.auth import get_password_hash
        raw = "mysecretpassword"
        hashed = get_password_hash(raw)
        assert hashed != raw
        assert raw not in hashed   # no substring either

    def test_correct_password_verifies(self):
        """verify_password returns True for the correct plaintext."""
        from app.utils.auth import get_password_hash, verify_password
        raw = "mysecretpassword"
        assert verify_password(raw, get_password_hash(raw)) is True

    def test_wrong_password_fails_verification(self):
        """verify_password returns False for any other string."""
        from app.utils.auth import get_password_hash, verify_password
        hashed = get_password_hash("correct")
        assert verify_password("wrong", hashed) is False
