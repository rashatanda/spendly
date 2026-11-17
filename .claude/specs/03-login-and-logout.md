# Spec: Login and Logout

## Overview
Implement login and logout so registered users can authenticate into Spendly and end their session. This is Step 3 of the roadmap and the first time the app verifies credentials against the database, sets a session on success, and clears it on logout. It also introduces route-level access control — pages that require a login will redirect unauthenticated users to `/login`. Every subsequent authenticated feature (profile, expenses) depends on the session contract established here.

## Depends on
- Step 1 — Database setup (`database/db.py` with `get_db()`, `users` table)
- Step 2 — Registration (a user must exist to log in)

## Schema note
`database/db.py` creates the `users` table with columns `name` and `password_hash`, but `app.py` and spec 02 reference `username` and `password`. Before implementing, reconcile the schema: either rename the columns in `init_db()` or update all query references. The spec assumes `username` and `password_hash` as the canonical column names — confirm with the actual DB before writing any SQL.

## Routes
- `GET /login` — render the login form — public
- `POST /login` — verify credentials, set session, redirect on success — public
- `GET /logout` — clear session, redirect to `/` — logged-in (or public with graceful no-op)

## Database changes
No new tables or columns required. The `users` table already has `username` (or `name`) and `password_hash` (or `password`). Confirm column names against `database/db.py` before writing queries.

## Templates
- **Modify:** `templates/login.html` — currently a stub; replace with a working form containing `username` and `password` fields; display flashed error messages; extend `base.html`

## Files to change
- `app.py` — replace the GET-only `/login` stub with GET+POST logic; replace the placeholder `/logout` route with real session-clearing logic
- `templates/login.html` — build out the login form

## Files to create
No new files required.

## New dependencies
No new dependencies. `werkzeug.security.check_password_hash` ships with Flask.

## Rules for implementation
- No SQLAlchemy or ORMs — use raw `sqlite3` via `get_db()`
- Parameterised queries only — no f-strings or `%` formatting in SQL
- Verify passwords with `werkzeug.security.check_password_hash`
- Never reveal which field (username vs password) was wrong — use a generic "Invalid username or password" message
- On success: store `user_id` and `username` in `session`, redirect to `/` (or `/expenses` once it exists)
- On logout: call `session.clear()`, then redirect to `/`
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`

## Definition of done
- [ ] `GET /login` renders the form without errors
- [ ] Submitting with both fields empty shows a validation error
- [ ] Submitting with a non-existent username shows "Invalid username or password"
- [ ] Submitting with a correct username but wrong password shows "Invalid username or password"
- [ ] A valid submission sets `session["user_id"]` and redirects (not shows the form again)
- [ ] After login, the navbar reflects the logged-in state (e.g. shows "Logout" link)
- [ ] `GET /logout` clears the session and redirects to `/`
- [ ] Visiting `/logout` when already logged out does not crash — it redirects cleanly
- [ ] After logout, `session` no longer contains `user_id`
