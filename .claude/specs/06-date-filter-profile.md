# Spec: Date Filter for Profile Page

## Overview
Step 6 adds a date-range filter to the profile page so users can narrow the
transaction list, summary stats, and category breakdown to a chosen time
window. Currently all four data sections always show every expense ever
recorded. After this step, the page will accept optional `start_date` and
`end_date` query parameters and pass them through to every query helper, so
the displayed figures reflect only the filtered period. This is a pure
backend + template wiring step — no new tables or routes are needed.

## Depends on
- Step 1: Database setup (`expenses` table with `date` column exists)
- Step 2: Registration (users stored in DB)
- Step 3: Login / Logout (`session["user_id"]` set on login)
- Step 4: Profile page static UI (template already renders all four sections)
- Step 5: Backend connection (`database/queries.py` helpers exist and are wired into `/profile`)

## Routes
- `GET /profile?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD` — filtered profile view — logged-in only

Both query params are optional. When omitted the page behaves exactly as before
(all expenses shown). No new route is registered; the existing `GET /profile`
route is extended.

## Database changes
No database changes. The `expenses.date` column (TEXT, ISO format `YYYY-MM-DD`)
already exists and supports range comparisons with `BETWEEN` or `>=`/`<=`.

## Templates
- **Modify**: `templates/profile.html`
  - Add a filter form above the transaction list with two date inputs
    (`start_date`, `end_date`) and a "Filter" submit button that issues a GET
    request to `/profile`.
  - Display the active filter range when one is applied (e.g. "Showing
    1 Nov 2026 – 15 Nov 2026").
  - Add a "Clear filter" link that returns to `/profile` with no params.
  - All four dynamic sections (stats, transactions, breakdown) must visually
    reflect the filtered data — no section should ever show unfiltered totals
    while another shows filtered ones.

## Files to change
- `app.py` — read `start_date` and `end_date` from `request.args` in the
  `profile()` view and forward them to every query helper call
- `database/queries.py` — update all four helpers to accept optional
  `start_date` and `end_date` kwargs; add `WHERE` / `AND` clauses that filter
  `expenses.date` when either param is provided
- `templates/profile.html` — add the filter form and active-filter indicator

## Files to create
No new files.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — raw `sqlite3` only via `get_db()`
- Parameterised queries only — never string-format values into SQL
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Currency must always display as ₹ — never £ or $
- Both `start_date` and `end_date` are optional; each helper must work
  correctly when either, both, or neither is supplied
- Date strings passed to queries must be in `YYYY-MM-DD` format; validate
  that any user-supplied value matches this format in the route before passing
  it to the helpers — silently ignore malformed values (treat as if not
  supplied)
- `get_summary_stats`, `get_recent_transactions`, and `get_category_breakdown`
  signatures become:
  ```
  get_summary_stats(user_id, start_date=None, end_date=None)
  get_recent_transactions(user_id, limit=10, start_date=None, end_date=None)
  get_category_breakdown(user_id, start_date=None, end_date=None)
  ```
  `get_user_by_id` does not need date params (user data is not date-filtered)
- The filter form must use `method="get"` so the URL is bookmarkable
- Do not add pagination in this step

## Definition of done
- [ ] Visiting `/profile` with no query params shows all expenses (behaviour unchanged from Step 5)
- [ ] Visiting `/profile?start_date=2026-11-01&end_date=2026-11-07` shows only expenses from 1–7 Nov 2026 for the seed user (4 transactions, total ₹5000.00)
- [ ] Summary stats (total, count, top category) update correctly for the filtered range
- [ ] Category breakdown reflects only the filtered expenses
- [ ] The filter form is visible on the profile page and pre-fills with the current filter values
- [ ] Submitting the filter form with valid dates redirects to the correct filtered URL
- [ ] A "Clear filter" link navigates back to `/profile` with no params
- [ ] Supplying a malformed date (e.g. `start_date=not-a-date`) does not crash the app — it is silently ignored and all expenses are shown
- [ ] A new user with no expenses sees ₹0.00, 0 transactions, and no category rows — both with and without a date filter
