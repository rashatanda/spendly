from datetime import datetime
from database.db import get_db


def get_user_by_id(user_id):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT name, email, created_at FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        return None

    try:
        dt = datetime.fromisoformat(row["created_at"])
        member_since = dt.strftime("%B %Y")
    except (ValueError, TypeError):
        member_since = row["created_at"]

    return {"name": row["name"], "email": row["email"], "member_since": member_since}


def get_summary_stats(user_id):
    conn = get_db()
    try:
        total_row = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) AS total, COUNT(*) AS cnt FROM expenses WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        top_row = conn.execute(
            """SELECT category, SUM(amount) AS cat_total
               FROM expenses WHERE user_id = ?
               GROUP BY category ORDER BY cat_total DESC LIMIT 1""",
            (user_id,),
        ).fetchone()
    finally:
        conn.close()

    return {
        "total_spent": total_row["total"],
        "transaction_count": total_row["cnt"],
        "top_category": top_row["category"] if top_row else "—",
    }


def get_recent_transactions(user_id, limit=10):
    conn = get_db()
    try:
        rows = conn.execute(
            """SELECT date, description, category, amount
               FROM expenses WHERE user_id = ?
               ORDER BY date DESC, id DESC LIMIT ?""",
            (user_id, limit),
        ).fetchall()
    finally:
        conn.close()

    return [dict(r) for r in rows]


def get_category_breakdown(user_id):
    conn = get_db()
    try:
        rows = conn.execute(
            """SELECT category AS name, SUM(amount) AS amount
               FROM expenses WHERE user_id = ?
               GROUP BY category ORDER BY amount DESC""",
            (user_id,),
        ).fetchall()
    finally:
        conn.close()

    if not rows:
        return []

    total = sum(r["amount"] for r in rows)
    breakdown = [{"name": r["name"], "amount": r["amount"], "pct": round(r["amount"] / total * 100)} for r in rows]

    # Adjust largest category so percentages sum exactly to 100
    diff = 100 - sum(item["pct"] for item in breakdown)
    if diff != 0:
        breakdown[0]["pct"] += diff

    return breakdown
