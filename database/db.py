import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "spendly.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT    NOT NULL UNIQUE,
            email    TEXT    NOT NULL UNIQUE,
            password TEXT    NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS expenses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title       TEXT    NOT NULL,
            amount      REAL    NOT NULL,
            category    TEXT    NOT NULL,
            date        DATE    NOT NULL,
            notes       TEXT,
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()


def seed_db():
    conn = get_db()

    conn.execute(
        "INSERT OR IGNORE INTO users (username, email, password) VALUES (?, ?, ?)",
        ("demo", "demo@spendly.app", "hashed_password_placeholder"),
    )
    conn.commit()

    user = conn.execute("SELECT id FROM users WHERE username = 'demo'").fetchone()
    uid = user["id"]

    sample_expenses = [
        (uid, "Groceries",        1200.00, "Food",          "2026-11-01", "Weekly shop"),
        (uid, "Metro card top-up",  500.00, "Transport",    "2026-11-03", None),
        (uid, "Netflix",            649.00, "Entertainment","2026-11-05", "Monthly plan"),
        (uid, "Electricity bill",  2300.00, "Utilities",    "2026-11-07", "October bill"),
        (uid, "Lunch",              350.00, "Food",         "2026-11-10", "With colleagues"),
    ]

    conn.executemany(
        "INSERT INTO expenses (user_id, title, amount, category, date, notes) VALUES (?,?,?,?,?,?)",
        sample_expenses,
    )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    seed_db()
    print("Database initialised and seeded.")
