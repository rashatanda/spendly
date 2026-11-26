"""
Tests for the profile route: GET /profile and POST /profile (password change).
"""

import pytest
import database.db as db_module
from werkzeug.security import check_password_hash


# ---------------------------------------------------------------------------
# Profile view (GET /profile)
# ---------------------------------------------------------------------------

class TestProfileView:

    def test_profile_redirects_unauthenticated_user_to_login(self, client):
        response = client.get("/profile", follow_redirects=False)
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

    def test_profile_loads_for_logged_in_user(self, logged_in_client):
        response = logged_in_client.get("/profile")
        assert response.status_code == 200

    def test_profile_displays_username(self, logged_in_client):
        from tests.conftest import TEST_USER
        response = logged_in_client.get("/profile")
        assert TEST_USER["username"].encode() in response.data

    def test_profile_displays_email(self, logged_in_client):
        from tests.conftest import TEST_USER
        response = logged_in_client.get("/profile")
        assert TEST_USER["email"].encode() in response.data


# ---------------------------------------------------------------------------
# Password change (POST /profile)
# ---------------------------------------------------------------------------

class TestPasswordChange:

    def test_change_password_with_valid_data_succeeds(
        self, logged_in_client, registered_user
    ):
        response = logged_in_client.post(
            "/profile",
            data={
                "current_password": registered_user["password"],
                "new_password": "NewPassword456",
                "confirm_new_password": "NewPassword456",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"updated successfully" in response.data

    def test_change_password_actually_updates_hash_in_db(
        self, logged_in_client, registered_user
    ):
        new_pw = "UpdatedPass789"
        logged_in_client.post(
            "/profile",
            data={
                "current_password": registered_user["password"],
                "new_password": new_pw,
                "confirm_new_password": new_pw,
            },
        )

        conn = db_module.get_db()
        row = conn.execute(
            "SELECT password_hash FROM users WHERE id = ?",
            (registered_user["id"],),
        ).fetchone()
        conn.close()

        assert check_password_hash(row["password_hash"], new_pw)

    def test_change_password_with_wrong_current_password_shows_error(
        self, logged_in_client
    ):
        response = logged_in_client.post(
            "/profile",
            data={
                "current_password": "WrongCurrentPw",
                "new_password": "NewPassword456",
                "confirm_new_password": "NewPassword456",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"incorrect" in response.data

    def test_change_password_with_mismatched_new_passwords_shows_error(
        self, logged_in_client, registered_user
    ):
        response = logged_in_client.post(
            "/profile",
            data={
                "current_password": registered_user["password"],
                "new_password": "NewPassword456",
                "confirm_new_password": "DifferentPassword",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"do not match" in response.data

    def test_change_password_with_missing_fields_shows_error(
        self, logged_in_client, registered_user
    ):
        response = logged_in_client.post(
            "/profile",
            data={
                "current_password": registered_user["password"],
                "new_password": "",
                "confirm_new_password": "",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"required" in response.data

    def test_change_password_does_not_update_db_when_current_password_wrong(
        self, logged_in_client, registered_user
    ):
        """The old password hash must remain unchanged after a failed attempt."""
        conn = db_module.get_db()
        original_hash = conn.execute(
            "SELECT password_hash FROM users WHERE id = ?",
            (registered_user["id"],),
        ).fetchone()["password_hash"]
        conn.close()

        logged_in_client.post(
            "/profile",
            data={
                "current_password": "WrongPw",
                "new_password": "NewPassword456",
                "confirm_new_password": "NewPassword456",
            },
        )

        conn = db_module.get_db()
        after_hash = conn.execute(
            "SELECT password_hash FROM users WHERE id = ?",
            (registered_user["id"],),
        ).fetchone()["password_hash"]
        conn.close()

        assert original_hash == after_hash

    def test_profile_post_redirects_unauthenticated_user_to_login(self, client):
        response = client.post(
            "/profile",
            data={
                "current_password": "any",
                "new_password": "any",
                "confirm_new_password": "any",
            },
            follow_redirects=False,
        )
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]
