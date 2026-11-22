import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import app as flask_app
from database.db import init_db, seed_db


@pytest.fixture
def app(tmp_path, monkeypatch):
    db_file = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_file))

    import database.db as db_module
    monkeypatch.setattr(db_module, "DB_PATH", str(db_file))

    with flask_app.app_context():
        init_db()
        seed_db()

    flask_app.config["TESTING"] = True
    flask_app.config["SECRET_KEY"] = "test-secret"
    yield flask_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def seed_user_id(app):
    from database.db import get_db
    with app.app_context():
        conn = get_db()
        row = conn.execute("SELECT id FROM users WHERE email = 'demo@spendly.com'").fetchone()
        conn.close()
        return row["id"]
