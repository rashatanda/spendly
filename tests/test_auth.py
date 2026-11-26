"""
Tests for authentication routes: /register, /login, /logout.

Covers the feature contract — what the routes are *supposed to do* — not
implementation details.
"""

import pytest
from tests.conftest import TEST_USER


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

class TestRegister:

    def test_register_page_loads(self, client):
        response = client.get("/register")
        assert response.status_code == 200

    def test_register_with_valid_credentials_redirects_to_profile(self, client):
        response = client.post(
            "/register",
            data={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "StrongPass1",
                "confirm_password": "StrongPass1",
            },
            follow_redirects=False,
        )
        assert response.status_code == 302
        assert "/profile" in response.headers["Location"]

    def test_register_creates_user_in_database(self, client, app):
        import database.db as db_module

        client.post(
            "/register",
            data={
                "username": "dbuser",
                "email": "dbuser@example.com",
                "password": "StrongPass1",
                "confirm_password": "StrongPass1",
            },
        )

        conn = db_module.get_db()
        row = conn.execute(
            "SELECT name, email FROM users WHERE email = ?",
            ("dbuser@example.com",),
        ).fetchone()
        conn.close()

        assert row is not None
        assert row["name"] == "dbuser"

    def test_register_sets_session_after_signup(self, client):
        with client.session_transaction() as sess:
            assert "user_id" not in sess

        client.post(
            "/register",
            data={
                "username": "sessionuser",
                "email": "session@example.com",
                "password": "StrongPass1",
                "confirm_password": "StrongPass1",
            },
        )

        with client.session_transaction() as sess:
            assert "user_id" in sess
            assert sess["username"] == "sessionuser"

    def test_register_with_mismatched_passwords_shows_error(self, client):
        response = client.post(
            "/register",
            data={
                "username": "mismatch",
                "email": "mismatch@example.com",
                "password": "Password1",
                "confirm_password": "Password2",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"do not match" in response.data

    def test_register_with_missing_fields_shows_error(self, client):
        response = client.post(
            "/register",
            data={
                "username": "",
                "email": "missing@example.com",
                "password": "Password1",
                "confirm_password": "Password1",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"required" in response.data

    def test_register_with_duplicate_username_shows_error(self, client, registered_user):
        response = client.post(
            "/register",
            data={
                "username": registered_user["username"],
                "email": "different@example.com",
                "password": "Password1",
                "confirm_password": "Password1",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"taken" in response.data

    def test_register_with_duplicate_email_shows_error(self, client, registered_user):
        response = client.post(
            "/register",
            data={
                "username": "differentuser",
                "email": registered_user["email"],
                "password": "Password1",
                "confirm_password": "Password1",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"registered" in response.data

    def test_register_redirects_to_landing_when_already_logged_in(
        self, logged_in_client
    ):
        response = logged_in_client.get("/register", follow_redirects=False)
        assert response.status_code == 302
        assert "/" in response.headers["Location"]


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

class TestLogin:

    def test_login_page_loads(self, client):
        response = client.get("/login")
        assert response.status_code == 200

    def test_login_with_valid_credentials_redirects_to_landing(
        self, client, registered_user
    ):
        response = client.post(
            "/login",
            data={
                "email": registered_user["email"],
                "password": registered_user["password"],
            },
            follow_redirects=False,
        )
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/") or "/" in response.headers["Location"]

    def test_login_with_valid_credentials_sets_session(
        self, client, registered_user
    ):
        client.post(
            "/login",
            data={
                "email": registered_user["email"],
                "password": registered_user["password"],
            },
        )

        with client.session_transaction() as sess:
            assert sess.get("user_id") == registered_user["id"]
            assert sess.get("username") == registered_user["username"]

    def test_login_with_wrong_password_shows_error(self, client, registered_user):
        response = client.post(
            "/login",
            data={
                "email": registered_user["email"],
                "password": "WrongPassword",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Invalid" in response.data

    def test_login_with_unknown_email_shows_error(self, client):
        response = client.post(
            "/login",
            data={
                "email": "ghost@example.com",
                "password": "SomePassword",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Invalid" in response.data

    def test_login_with_missing_email_shows_error(self, client):
        response = client.post(
            "/login",
            data={"email": "", "password": "Password1"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"required" in response.data

    def test_login_with_missing_password_shows_error(self, client):
        response = client.post(
            "/login",
            data={"email": "user@example.com", "password": ""},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"required" in response.data

    def test_login_redirects_to_landing_when_already_logged_in(
        self, logged_in_client
    ):
        response = logged_in_client.get("/login", follow_redirects=False)
        assert response.status_code == 302


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------

class TestLogout:

    def test_logout_clears_session(self, logged_in_client):
        with logged_in_client.session_transaction() as sess:
            assert "user_id" in sess

        logged_in_client.get("/logout")

        with logged_in_client.session_transaction() as sess:
            assert "user_id" not in sess

    def test_logout_redirects_to_landing(self, logged_in_client):
        response = logged_in_client.get("/logout", follow_redirects=False)
        assert response.status_code == 302
        assert "/" in response.headers["Location"]

    def test_logout_shows_confirmation_message(self, logged_in_client):
        response = logged_in_client.get("/logout", follow_redirects=True)
        assert response.status_code == 200
        assert b"logged out" in response.data
