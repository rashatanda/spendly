"""
Pytest fixtures for Spendly tests.

Each test function gets a fresh in-memory-equivalent SQLite database by
redirecting database.db.DB_PATH to a temporary file, so tests never touch
the real spendly.db and are fully isolated from one another.
"""

import os
import tempfile

import pytest
from werkzeug.security import generate_password_hash

import database.db as db_module
from app import app as flask_app


# ---------------------------------------------------------------------------
# Core fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def app(tmp_path):
    """
    Yield a configured Flask test application backed by a fresh temporary
    SQLite database.  DB_PATH is restored after each test.
    """
    db_file = str(tmp_path / "test_spendly.db")

    original_path = db_module.DB_PATH
    db_module.DB_PATH = db_file

    flask_app.config.update(
        TESTING=True,
        SECRET_KEY="test-secret-key",
        WTF_CSRF_ENABLED=False,
    )

    with flask_app.app_context():
        db_module.init_db()   # creates tables in the temp DB

    yield flask_app

    db_module.DB_PATH = original_path
    if os.path.exists(db_file):
        os.remove(db_file)


@pytest.fixture()
def client(app):
    """Return a Flask test client with a persistent session cookie jar."""
    return app.test_client()


# ---------------------------------------------------------------------------
# User fixtures
# ---------------------------------------------------------------------------

TEST_USER = {
    "username": "testuser",
    "email": "testuser@example.com",
    "password": "Password123",
}


@pytest.fixture()
def registered_user(app):
    """
    Insert a test user directly into the DB and return their credentials dict.
    Does NOT log the user in — use the `logged_in_client` fixture for that.
    """
    conn = db_module.get_db()
    try:
        conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (
                TEST_USER["username"],
                TEST_USER["email"],
                generate_password_hash(TEST_USER["password"]),
            ),
        )
        conn.commit()
        row = conn.execute(
            "SELECT id FROM users WHERE email = ?", (TEST_USER["email"],)
        ).fetchone()
        user_id = row["id"]
    finally:
        conn.close()

    return {**TEST_USER, "id": user_id}


@pytest.fixture()
def logged_in_client(client, registered_user):
    """
    Return a test client that is already authenticated as the test user.
    """
    client.post(
        "/login",
        data={
            "email": registered_user["email"],
            "password": registered_user["password"],
        },
        follow_redirects=True,
    )
    return client
