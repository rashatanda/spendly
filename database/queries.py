from datetime import datetime
from database.db import get_db


def _date_where(start_date, end_date):
    conditions = ["user_id = ?"]
    extra_params = []
    if start_date:
        conditions.append("date >= ?")
        extra_params.append(start_date)
    if end_date:
        conditions.append("date <= ?")
        extra_params.append(end_date)
    return " AND ".join(conditions), extra_params


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


def get_summary_stats(user_id, start_date=None, end_date=None):
    where, extra = _date_where(start_date, end_date)
    params = [user_id] + extra
    conn = get_db()
    try:
        total_row = conn.execute(
            f"SELECT COALESCE(SUM(amount), 0) AS total, COUNT(*) AS cnt FROM expenses WHERE {where}",
            params,
        ).fetchone()
        top_row = conn.execute(
            f"""SELECT category, SUM(amount) AS cat_total
               FROM expenses WHERE {where}
               GROUP BY category ORDER BY cat_total DESC LIMIT 1""",
            params,
        ).fetchone()
    finally:
        conn.close()

    return {
        "total_spent": total_row["total"],
        "transaction_count": total_row["cnt"],
        "top_category": top_row["category"] if top_row else "—",
    }


def get_recent_transactions(user_id, limit=10, start_date=None, end_date=None):
    where, extra = _date_where(start_date, end_date)
    params = [user_id] + extra + [limit]
    conn = get_db()
    try:
        rows = conn.execute(
            f"""SELECT date, description, category, amount
               FROM expenses WHERE {where}
               ORDER BY date DESC, id DESC LIMIT ?""",
            params,
        ).fetchall()
    finally:
        conn.close()

    return [dict(r) for r in rows]


def get_category_breakdown(user_id, start_date=None, end_date=None):
    where, extra = _date_where(start_date, end_date)
    params = [user_id] + extra
    conn = get_db()
    try:
        rows = conn.execute(
            f"""SELECT category AS name, SUM(amount) AS amount
               FROM expenses WHERE {where}
               GROUP BY category ORDER BY amount DESC""",
            params,
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
