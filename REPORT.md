# Architecture and Design Report — AI Commitment Tracker

Generated: 2026-06-07

---

## 1. Overview

This repository implements the "AI Commitment Tracker": a small Flask-based web application that stores user commitments, predicts their priority using a hybrid ML + rule-based system, and surfaces urgent items in a dashboard. The codebase is intentionally compact and organized into three main areas: `backend`, `database`, and `frontend` under the `webapp/` folder.

Repository entry points
- `run.py` — simple runtime launcher that imports the Flask app and runs it.
- `webapp/backend/app.py` — Flask application and route definitions (main server)

---

## 2. High-level architecture

User (Browser)
  ↔ HTTP
Flask App (`webapp/backend/app.py`)
  ↔ Database layer (`webapp/database/database.py`, SQLite `commitments.db`)
  ↔ ML / Priority Predictor (`webapp/backend/priority_predictor.py`, `priority_model.pkl`)
  ↔ Templates / Static (`webapp/frontend/templates`, `webapp/frontend/static`)

Key cross-cutting concerns: session management (Flask sessions), model loading (cached at startup), basic CORS, and server-side template rendering (Jinja2).

---

## 3. Components & Responsibilities

### 3.1 Backend (Flask) — `webapp/backend/app.py`
- Creates the Flask app with explicit `template_folder` and `static_folder` that point to `webapp/frontend`.
- Loads the ML model at startup via `load_model()` from `priority_predictor.py`.
- Initializes the `Database` class (SQLite) and exposes routes:
  - `GET /`, `GET|POST /login` — session-based login (username only)
  - `GET /dashboard` — render dashboard with user's commitments
  - `POST /add_commitment` — create a commitment; calls `predict_priority()` for automatic priority
  - `PUT /api/commitments/<id>/status` — update status (Pending/Completed/Overdue)
  - `DELETE /api/commitments/<id>` — delete commitment
  - `POST /api/predict_priority` — returns a predicted priority for client-side use
  - `POST /logout`, `POST /api/mark_urgent_shown`
- Performs server-side formatting for deadlines, urgency labels, and overdue detection.
- Uses session keys `user_id` and `username` for authentication state.

### 3.2 Database Layer — `webapp/database/database.py`
- Uses SQLite (`commitments.db`) and ensures `PRAGMA foreign_keys = ON`.
- Schema (created if missing):
  - `users` table: `id`, `username` (unique), `created_at`
  - `commitments` table: `id`, `user_id` (FK), `subject`, `description`, `deadline`, `status`, `priority`, `created_at`, `updated_at`
- Provides CRUD operations: `create_user`, `get_user_by_username`, `create_commitment`, `get_user_commitments`, `get_urgent_commitments`, `update_commitment_status`, `update_commitment`, `delete_commitment`.
- Query features: ordering by priority (via SQL CASE mapping) and deadline, filtering by status, limiting urgent items.
- Connection handling uses `sqlite3.connect(..., check_same_thread=False)` and `row_factory = sqlite3.Row`.

### 3.3 Priority Predictor (Hybrid AI) — `webapp/backend/priority_predictor.py`
- Purpose: combine a pre-trained scikit-learn model with deterministic rule-based logic.
- Model load process
  - Attempts to import `joblib` and load `priority_model.pkl` from the backend folder.
  - `load_model()` caches the model in module-level `_MODEL` so it loads once at app startup.
  - If `joblib` missing or model file absent, code falls back to deterministic defaults.
- Prediction flow
  1. Compute `hours_left` from given deadline (if provided).
  2. If model available, build input like `"<text> deadline_<hours>"` and call `model.predict()` to obtain base classification (`High`/`Medium`/`Low`). If model missing or fails, fallback `Medium`.
  3. Call `apply_priority_rules()` to apply safety rules that only upgrade (never downgrade) priority:
     - Financial keywords (`pay`, `rent`, `bill`, ...): upgrade Low→Medium
     - Professional/meeting keywords (`meeting`, `interview`, ...): upgrade Low→Medium
     - Time-based escalation: ≤24 hours → `High`, ≤72 hours and `Low` → `Medium`
     - Critical keywords + short deadline (≤12h) → `High`
- This hybrid approach ensures safety (avoid dangerous downgrades) and predictable escalation for urgent items.

### 3.4 Frontend — `webapp/frontend`
- Templates (Jinja2): `login.html`, `dashboard.html`
  - `dashboard.html` renders commitments list, shows urgency badges, supports filter links and sort-by-priority, and includes an urgent modal when high-priority items exist.
- Static assets
  - `static/css/style.css` — extensive styling (responsive, badges, modal, animations)
  - `static/js/dashboard.js` — minimal client-side behavior: logout, status updates (PUT), delete (DELETE), modal close, sort handling.
- The UI is server-rendered; API endpoints are used for dynamic actions (status update, delete, predict).

---

## 4. Data Flow (detailed)
1. User submits the add form on `/dashboard`.
2. `app.py` receives POST `/add_commitment` and parses `subject`, `description`, optional `deadline`.
3. Server computes `deadline_dt` and calls `predict_priority(commitment_text, deadline_dt)`.
4. `priority_predictor` loads model if necessary and returns final priority after rule application.
5. `Database.create_commitment()` inserts the record with priority and timestamps.
6. On subsequent views, `app.py` fetches commitments via `Database.get_user_commitments()`; for each commit it calculates display fields (`deadline_formatted`, `is_overdue`, `urgency` via `helpers.calculate_urgency`) and renders `dashboard.html`.

---

## 5. Database Schema (quick reference)
- `users`(id INTEGER PK, username TEXT UNIQUE, created_at TEXT)
- `commitments`(
    id INTEGER PK,
    user_id INTEGER FK -> users.id,
    subject TEXT,
    description TEXT,
    deadline TEXT (ISO format),
    status TEXT DEFAULT 'Pending',
    priority TEXT DEFAULT 'Medium',
    created_at TEXT,
    updated_at TEXT
  )

Indexes: none defined explicitly; for scale, consider indexes on `(user_id)`, `(user_id, status)`, and `(user_id, priority, deadline)`.

---

## 6. Security & Operational notes
- Authentication: minimal username-only login; sessions stored in Flask session cookie. Not suitable for production.
- `secret_key` is read from env var `SECRET_KEY` with insecure default `dev-secret-key` — MUST be changed for production.
- No CSRF protection on forms (Flask-WTF not used) — acceptable for demo, but add CSRF tokens in production.
- SQL safety: uses parameterized queries (safe from SQL injection in code shown).
- Model file loading: absence of `priority_model.pkl` is handled gracefully (fallback to `Medium`).
- Concurrency: SQLite with `check_same_thread=False` can handle light concurrent access; for heavier loads use PostgreSQL or another server DB.

---

## 7. Tests
- `webapp/backend/test_priority_rules.py` — simple CLI-style tests that exercise `apply_priority_rules()` and `predict_priority()` logic paths. These are not automated unit tests (no pytest harness), but can be executed directly.

---

## 8. Dependencies & Run
- Key dependencies listed in `requirements.txt`:
  - `Flask`, `flask-cors`, `gunicorn`, `joblib`, `scikit-learn`, `numpy`
- Run (development):

  python run.py

  or

  cd webapp/backend
  python app.py

- Notes: scikit-learn on Windows may require pre-built wheels. `INSTALL.md` documents recommended installation steps.

---

## 9. Observations & Recommended Improvements
- Authentication & Security
  - Add password support, hashed storage, and CSRF protection. Use Flask-Login for session management.
  - Move `secret_key` to an environment variable and avoid default in code.
- Tests & CI
  - Convert `test_priority_rules.py` into a proper pytest suite and add CI to run tests on each push.
- Model & ML lifecycle
  - Add model versioning and a small management script to re-train and export `priority_model.pkl`.
  - Add input validation and metrics logging for model predictions (counts of High/Medium/Low over time).
- Performance & Scale
  - Replace SQLite with a server DB for multi-user concurrency (Postgres).
  - Add indexes for common query patterns.
- UX
  - Add AJAX form for adding commitments to avoid full page reloads.
  - Add client-side validation for deadlines and better error messages.

---

## 10. Files of interest (quick links)
- App: [webapp/backend/app.py](webapp/backend/app.py)
- Predictor: [webapp/backend/priority_predictor.py](webapp/backend/priority_predictor.py)
- Helpers: [webapp/backend/helpers.py](webapp/backend/helpers.py)
- DB: [webapp/database/database.py](webapp/database/database.py)
- Templates: [webapp/frontend/templates/dashboard.html](webapp/frontend/templates/dashboard.html), [webapp/frontend/templates/login.html](webapp/frontend/templates/login.html)
- Static: [webapp/frontend/static/js/dashboard.js](webapp/frontend/static/js/dashboard.js), [webapp/frontend/static/css/style.css](webapp/frontend/static/css/style.css)

---

## 11. Conclusion
The project is a well-structured small Flask app with a pragmatic hybrid ML + rules approach for priority prediction. It is ready for local usage and experimentation. For production-readiness, implement authentication hardening, proper testing/CI, and a more robust datastore.


---

Report generated and saved in repository root as `REPORT.md`.
