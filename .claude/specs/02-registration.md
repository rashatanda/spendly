# Spec: Registration

## Overview
Implement user registration so new visitors can create a Spendly account. This is Step 2 of the roadmap and the first time the app writes a real user to the database. It introduces form handling, password hashing, flash messaging, and session-based login-on-success — all patterns that every subsequent authenticated feature relies on.

## Depends on
- Step 1 — Database setup (`database/db.py` with `get_db()`, `init_db()`, `users` table)

## Routes
- `GET /register` — render the registration form — public
- `POST /register` — handle form submission, create user, redirect on success — public

## Database changes
No new tables or columns. The `users` table already exists with the correct schema:
```
id, username, email, password, created_at
```
Confirm `database/db.py` has the `users` table before implementing.

## Templates
- **Modify:** `templates/register.html` — currently a stub; replace with a working form containing fields: `username`, `email`, `password`, `confirm_password`; display flashed error/success messages; extend `base.html`

## Files to change
- `app.py` — replace the GET-only `/register` route with GET+POST logic
- `templates/register.html` — build out the registration form

## Files to create
No new files required.

## New dependencies
No new dependencies. `werkzeug.security` ships with Flask.

## Rules for implementation
- No SQLAlchemy or ORMs — use raw `sqlite3` via `get_db()`
- Parameterised queries only — no f-strings or `%` formatting in SQL
- Hash passwords with `werkzeug.security.generate_password_hash` before storing
- Validate server-side: all fields required, passwords must match, username and email must be unique
- On validation error: re-render form with a flashed error message (do not wipe fields)
- On success: insert user, store `user_id` and `username` in `session`, redirect to `/` (or `/expenses` once that exists)
- Set `app.secret_key` in `app.py` (use `os.urandom(24)` or a fixed dev key via env var)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`

## Definition of done
- [ ] `GET /register` renders the form without errors
- [ ] Submitting with all fields empty shows a validation error
- [ ] Submitting with mismatched passwords shows a validation error
- [ ] Registering with an existing username shows a "username taken" error
- [ ] Registering with an existing email shows an "email already registered" error
- [ ] A valid submission inserts a new row in `users` with a hashed password (verify via `sqlite3 database/spendly.db "SELECT username, password FROM users"`)
- [ ] After successful registration the user is redirected (not shown the form again)
- [ ] The session contains `user_id` after successful registration
