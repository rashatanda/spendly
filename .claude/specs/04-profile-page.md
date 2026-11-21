# Spec: Profile Page

## Overview
Step 4 replaces the `/profile` placeholder with a real page that lets a logged-in user view their account details (username, email, member-since date) and change their password. It is the first authenticated-only page in Spendly and establishes the pattern — session guard, flash feedback, template extending `base.html` — that all future protected routes will follow.

## Depends on
- Step 1 — Database setup (`users` table must exist)
- Step 2 — Registration (creates user rows)
- Step 3 — Login / logout (session variables `user_id` and `username` must be set)

## Routes
- `GET  /profile`      — render profile page with current user data — logged-in only
- `POST /profile`      — handle change-password form submission — logged-in only

## Database changes
No new tables or columns. The existing `users` table (id, name, email, password_hash, created_at) has everything needed.

## Templates
- **Create:** `templates/profile.html` — profile page extending `base.html`; shows username, email, created_at; contains a change-password form with fields `current_password`, `new_password`, `confirm_new_password`
- **Modify:** none

## Files to change
- `app.py` — replace the placeholder `/profile` route with the full GET + POST implementation

## Files to create
- `templates/profile.html`

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — raw `sqlite3` via `get_db()` only
- Parameterised queries only — no string formatting in SQL
- Passwords hashed with `werkzeug.security` (`generate_password_hash`, `check_password_hash`)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Redirect to `/login` (with a flash message) if `session["user_id"]` is not set
- Flash success or error after every POST — never silently succeed or fail
- Close the DB connection in a `finally` block every time
- Amounts and currency display: use ₹ (INR), never $

## Definition of done
- [ ] Visiting `/profile` while logged out redirects to `/login` with a flash message
- [ ] Visiting `/profile` while logged in renders the page showing the correct username, email, and member-since date
- [ ] Submitting the change-password form with a wrong current password flashes an error and does not update the hash
- [ ] Submitting the change-password form with mismatched new passwords flashes an error and does not update the hash
- [ ] Submitting the change-password form with valid data updates `password_hash` in the DB, flashes success, and the user can log in with the new password
- [ ] The page passes `pytest` (no existing tests broken)
