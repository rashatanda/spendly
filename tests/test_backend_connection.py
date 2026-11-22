from database.queries import (
    get_user_by_id,
    get_summary_stats,
    get_recent_transactions,
    get_category_breakdown,
)


# ------------------------------------------------------------------ #
# get_user_by_id                                                      #
# ------------------------------------------------------------------ #

def test_get_user_by_id_valid(app, seed_user_id):
    with app.app_context():
        user = get_user_by_id(seed_user_id)
    assert user is not None
    assert user["name"] == "Demo User"
    assert user["email"] == "demo@spendly.com"
    assert "member_since" in user
    assert user["member_since"]  # non-empty string


def test_get_user_by_id_nonexistent(app):
    with app.app_context():
        result = get_user_by_id(999999)
    assert result is None


# ------------------------------------------------------------------ #
# get_summary_stats                                                   #
# ------------------------------------------------------------------ #

def test_get_summary_stats_with_expenses(app, seed_user_id):
    with app.app_context():
        stats = get_summary_stats(seed_user_id)
    assert stats["transaction_count"] == 8
    assert abs(stats["total_spent"] - 9449.00) < 0.01
    assert stats["top_category"] == "Shopping"


def test_get_summary_stats_no_expenses(app):
    from database.db import get_db
    with app.app_context():
        conn = get_db()
        conn.execute("INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                     ("Empty User", "empty@spendly.com", "x"))
        conn.commit()
        uid = conn.execute("SELECT id FROM users WHERE email = 'empty@spendly.com'").fetchone()["id"]
        conn.close()
        stats = get_summary_stats(uid)
    assert stats["total_spent"] == 0
    assert stats["transaction_count"] == 0
    assert stats["top_category"] == "—"


# ------------------------------------------------------------------ #
# get_recent_transactions                                             #
# ------------------------------------------------------------------ #

def test_get_recent_transactions_with_expenses(app, seed_user_id):
    with app.app_context():
        txns = get_recent_transactions(seed_user_id)
    assert len(txns) == 8
    dates = [t["date"] for t in txns]
    assert dates == sorted(dates, reverse=True)
    assert all(k in txns[0] for k in ("date", "description", "category", "amount"))


def test_get_recent_transactions_no_expenses(app):
    from database.db import get_db
    with app.app_context():
        conn = get_db()
        conn.execute("INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                     ("Empty2", "empty2@spendly.com", "x"))
        conn.commit()
        uid = conn.execute("SELECT id FROM users WHERE email = 'empty2@spendly.com'").fetchone()["id"]
        conn.close()
        result = get_recent_transactions(uid)
    assert result == []


# ------------------------------------------------------------------ #
# get_category_breakdown                                              #
# ------------------------------------------------------------------ #

def test_get_category_breakdown_with_expenses(app, seed_user_id):
    with app.app_context():
        bd = get_category_breakdown(seed_user_id)
    assert len(bd) == 7
    assert sum(item["pct"] for item in bd) == 100
    amounts = [item["amount"] for item in bd]
    assert amounts == sorted(amounts, reverse=True)
    assert all(k in bd[0] for k in ("name", "amount", "pct"))


def test_get_category_breakdown_no_expenses(app):
    from database.db import get_db
    with app.app_context():
        conn = get_db()
        conn.execute("INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                     ("Empty3", "empty3@spendly.com", "x"))
        conn.commit()
        uid = conn.execute("SELECT id FROM users WHERE email = 'empty3@spendly.com'").fetchone()["id"]
        conn.close()
        result = get_category_breakdown(uid)
    assert result == []


# ------------------------------------------------------------------ #
# Route: GET /profile                                                 #
# ------------------------------------------------------------------ #

def test_profile_unauthenticated(client):
    response = client.get("/profile")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_profile_authenticated(client, app, seed_user_id):
    with client.session_transaction() as sess:
        sess["user_id"] = seed_user_id
        sess["username"] = "Demo User"

    response = client.get("/profile")
    assert response.status_code == 200
    body = response.data.decode()
    assert "Demo User" in body
    assert "demo@spendly.com" in body
    assert "₹" in body
    assert "9449.00" in body
    assert "Shopping" in body
