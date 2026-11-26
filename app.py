import os
import re

from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

from database.db import get_db, init_db, seed_db
from database.queries import get_user_by_id, get_summary_stats, get_recent_transactions, get_category_breakdown

_DATE_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$")


def _valid_date(val):
    return val if val and _DATE_RE.match(val) else None


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-in-prod")

with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("landing"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not all([username, email, password, confirm_password]):
            flash("All fields are required.")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match.")
            return render_template("register.html")

        conn = get_db()
        try:
            if conn.execute("SELECT id FROM users WHERE name = ?", (username,)).fetchone():
                flash("Username already taken.")
                return render_template("register.html")

            if conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone():
                flash("Email already registered.")
                return render_template("register.html")

            hashed = generate_password_hash(password)
            cur = conn.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                (username, email, hashed),
            )
            conn.commit()
            session["user_id"] = cur.lastrowid
            session["username"] = username
            session.pop("_flashes", None)
        finally:
            conn.close()

        return redirect(url_for("profile"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("landing"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Email and password are required.")
            return render_template("login.html")

        conn = get_db()
        try:
            row = conn.execute(
                "SELECT id, name, password_hash FROM users WHERE email = ?", (email,)
            ).fetchone()
        finally:
            conn.close()

        if row is None or not check_password_hash(row["password_hash"], password):
            flash("Invalid email or password.")
            return render_template("login.html")

        session["user_id"] = row["id"]
        session["username"] = row["name"]
        session.pop("_flashes", None)
        flash(f"Welcome back, {row['name']}!", "success")
        return redirect(url_for("landing"))

    return render_template("login.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("landing"))


@app.route("/profile", methods=["GET", "POST"])
def profile():
    if not session.get("user_id"):
        flash("Please sign in to view your profile.")
        return redirect(url_for("login"))

    if request.method == "POST":
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_new = request.form.get("confirm_new_password", "")

        if not all([current_password, new_password, confirm_new]):
            flash("All fields are required.")
            return redirect(url_for("profile"))

        conn = get_db()
        try:
            row = conn.execute(
                "SELECT password_hash FROM users WHERE id = ?",
                (session["user_id"],)
            ).fetchone()

            if not check_password_hash(row["password_hash"], current_password):
                flash("Current password is incorrect.")
                return redirect(url_for("profile"))

            if new_password != confirm_new:
                flash("New passwords do not match.")
                return redirect(url_for("profile"))

            conn.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (generate_password_hash(new_password), session["user_id"])
            )
            conn.commit()
        finally:
            conn.close()

        flash("Password updated successfully.", "success")
        return redirect(url_for("profile"))

    uid = session["user_id"]
    start_date = _valid_date(request.args.get("start_date", ""))
    end_date = _valid_date(request.args.get("end_date", ""))

    user = get_user_by_id(uid)
    stats = get_summary_stats(uid, start_date, end_date)
    transactions = get_recent_transactions(uid, start_date=start_date, end_date=end_date)
    breakdown = get_category_breakdown(uid, start_date, end_date)

    return render_template("profile.html", user=user, stats=stats,
                           transactions=transactions, breakdown=breakdown,
                           start_date=start_date, end_date=end_date)


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
