# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies (use the venv)
python -m venv venv
venv\Scripts\activate      # Windows
pip install -r requirements.txt

# Run the app
python app.py              # serves on http://localhost:5001

# Run tests
pytest

# Run a single test file
pytest tests/test_auth.py
```

## Architecture

**Spendly** is a Flask expense-tracker web app built as a step-by-step learning project. The app uses Flask + SQLite (no ORM) and Jinja2 templates.

- `app.py` — all routes; currently only landing/auth/legal pages are implemented; expense and profile routes return placeholder strings pending student implementation
- `database/db.py` — stub for `get_db()`, `init_db()`, `seed_db()`; students write this in Step 1 using raw SQLite with `row_factory` and foreign keys enabled
- `templates/base.html` — shared layout (navbar + footer); all pages extend this
- `templates/` — Jinja2 templates; `landing.html` is the most developed, others are stubs
- `static/css/style.css` — single stylesheet; fonts are DM Serif Display + DM Sans (Google Fonts)
- `static/js/main.js` — minimal JS placeholder

## Planned steps (from `file.txt`)

The repo is structured around incremental student steps:
1. Database setup (`database/db.py`)
2. Register / login with session management
3. Logout
4. Profile page
5–9. CRUD for expenses

New routes go in `app.py`; DB helpers go in `database/db.py`; every new page template should extend `base.html`.
