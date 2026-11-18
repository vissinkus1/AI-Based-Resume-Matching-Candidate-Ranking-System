# DECISIONS

> Every technical decision and why, one line each.
> Append-only — do not remove earlier entries.

## Phase 0

| # | Decision | Rationale |
|---|----------|-----------|
| D1 | Backend app lives in `backend/app/` with `main.py` as the FastAPI entrypoint | Standard FastAPI layout; keeps routers/services/models cleanly separated. |
| D2 | `backend/run.py` as a convenience script to start Uvicorn | Avoids long CLI commands; documents the default host/port in one place. |
| D3 | SQLAlchemy async is NOT used; synchronous engine + `SessionLocal` instead | Simpler to explain in interview; SQLite has limited async support; prototype scope. |
| D4 | `DATABASE_URL` defaults to `sqlite:///./resume_matcher.db` | Zero-config dev setup; PostgreSQL swap via env var later. |
| D5 | Scoring weights stored in `backend/app/core/scoring_config.py` as a frozen dataclass | Single importable Python object; easy to explain, test, and tune. |
| D6 | Frontend created manually (not via `create-vite` wizard) for full control over initial files | Avoids wizard-generated boilerplate we'd immediately delete. |
| D7 | Tailwind CSS via PostCSS (standard setup) | Vite + PostCSS is the recommended Tailwind path; simple and fast. |
| D8 | Axios instance in `frontend/src/api/client.js` with `baseURL` pointing to `http://localhost:8000` | Single place to change the backend URL; interceptors can be added later. |
| D9 | pnpm as the Node package manager | Already available in the environment; faster and more disk-efficient than npm. |
