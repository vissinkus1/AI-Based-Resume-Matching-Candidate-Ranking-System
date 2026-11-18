# PROGRESS

> Updated at the end of every phase. Read at the start of every session.

## Phase 0 — Setup & Context Files

**Status:** ✅ DONE

### Checklist

- [x] Repo directories: `/backend`, `/frontend`, `/sample_data`, `/docs`
- [x] `PROJECT_CONTEXT.md`, `PROGRESS.md`, `DECISIONS.md`
- [x] `.gitignore`, root `README.md` stub
- [x] Backend: FastAPI modular structure (routers, services, models, schemas,
      db, core/config), venv, `requirements.txt`, CORS, SQLAlchemy +
      DATABASE_URL, `/health` endpoint (checks DB)
- [x] Scoring-weights config file (`backend/app/core/scoring_config.py`)
- [x] Frontend: React + Vite + Tailwind + Axios + React Router, layout/navbar,
      placeholder pages (`/`, `/dashboard`, `/candidate/:id`), `/health` call
- [x] Deps installed, both servers verified running

### Files Created

```
Root:
  .gitignore
  DECISIONS.md
  PROGRESS.md
  PROJECT_CONTEXT.md
  README.md

Backend (backend/):
  requirements.txt
  run.py
  app/__init__.py
  app/main.py                     # FastAPI app, CORS, lifespan
  app/core/__init__.py
  app/core/config.py              # Settings from env vars
  app/core/scoring_config.py      # Frozen dataclass with all weights
  app/db/__init__.py
  app/db/database.py              # Engine, SessionLocal, Base
  app/db/session.py               # get_db dependency
  app/models/__init__.py
  app/routers/__init__.py
  app/routers/health.py           # GET /health (checks DB)
  app/schemas/__init__.py
  app/services/__init__.py

Frontend (frontend/):
  index.html
  package.json
  package-lock.json
  postcss.config.js
  tailwind.config.js
  vite.config.js
  src/main.jsx                    # Entry point with BrowserRouter
  src/App.jsx                     # Routes definition
  src/index.css                   # Tailwind layers
  src/api/client.js               # Axios instance
  src/components/Layout.jsx       # Shared page wrapper
  src/components/Navbar.jsx       # Top navigation bar
  src/pages/Home.jsx              # Upload page + /health status
  src/pages/Dashboard.jsx         # Ranking table placeholder
  src/pages/CandidateDetail.jsx   # Detail view placeholder

Other:
  docs/.gitkeep
  sample_data/.gitkeep
```

### Test Results

| Test | Result |
|------|--------|
| `from app.main import app` — imports cleanly | ✅ Pass |
| Scoring weights validate (sum = 1.0) | ✅ Pass |
| `GET /health` → `{"status":"healthy","api":true,"database":true}` | ✅ Pass (HTTP 200) |
| `vite build` — production build completes | ✅ Pass (5.65 s, 103 modules) |
| `vite dev` — dev server starts on port 5173 | ✅ Pass |

### Known Issues

- None.

---

## Phase 1 — JD Module
**Status:** TODO

## Phase 2 — Resume Parsing
**Status:** TODO

## Phase 3 — Matching Engine
**Status:** TODO

## Phase 4 — API + DB Integration
**Status:** TODO

## Phase 5 — Ranking Dashboard
**Status:** TODO

## Phase 6 — Candidate Detail View
**Status:** TODO

## Phase 7 — Synthetic Data + Testing + Fixes
**Status:** TODO

## Phase 8 — README, Algorithm Doc, Demo, Polish
**Status:** TODO
