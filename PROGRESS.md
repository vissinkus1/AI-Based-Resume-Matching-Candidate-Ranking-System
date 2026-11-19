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
**Status:** ✅ DONE

### Checklist

- [x] Shared text extraction service (`backend/app/services/text_extractor.py`) for PDF, DOCX (paragraphs + tables), and TXT
- [x] Clear custom exceptions (`backend/app/core/exceptions.py`): UnsupportedFileTypeError, EmptyFileError, ScannedPDFError, CorruptFileError
- [x] Curated skills taxonomy (`backend/app/data/skills_taxonomy.json`) with 327 canonical skills and 700+ aliases across 12 categories
- [x] Fast taxonomy loader and O(1) lookup service (`backend/app/services/skills_taxonomy.py`)
- [x] JD parser service (`backend/app/services/jd_parser.py`): spaCy PhraseMatcher with whole-word boundary verification, required vs preferred classification, numeric & word-number experience ranges, normalized qualification levels, responsibilities extraction, and filtered noun-chunk keywords
- [x] SQLAlchemy JobDescription model (`backend/app/models/jd.py`) and repository (`backend/app/repositories/jd_repository.py`)
- [x] Pydantic schemas (`backend/app/schemas/jd.py`) for request/response validation
- [x] RESTful API endpoints (`backend/app/routers/jd.py`): POST /parse (text or file), GET /{id}, GET (list), PUT /{id} (recruiter edit), DELETE /{id}
- [x] Frontend JD module in `frontend/src/pages/Home.jsx`: Paste Text / Upload File tabs, drag-and-drop, Analyze button, results card, editable SkillChips with remove/add/toggle category, and Save changes
- [x] Global React `JDContext` (`frontend/src/context/JDContext.jsx`) and API client (`frontend/src/api/jd.js`)
- [x] 3 realistic synthetic sample JDs in `sample_data/jds/`: Java backend (.txt), React frontend (.docx), AI/ML engineer (.pdf)
- [x] 52 automated tests in pytest (`test_jd_parser.py`, `test_jd_api.py`) with 100% pass rate

### Files Created / Modified

```
Backend:
  backend/app/core/config.py              # Pydantic v2 SettingsConfigDict
  backend/app/core/exceptions.py          # Custom domain exceptions
  backend/app/data/skills_taxonomy.json   # 327 skills, 700+ aliases
  backend/app/models/jd.py                # JobDescription SQLAlchemy model
  backend/app/models/__init__.py          # Export JobDescription
  backend/app/repositories/jd_repository.py # Repository CRUD pattern
  backend/app/repositories/__init__.py
  backend/app/routers/jd.py               # REST API endpoints (/api/jd)
  backend/app/routers/__init__.py
  backend/app/schemas/jd.py               # Request/response validation schemas
  backend/app/services/text_extractor.py  # Shared PDF/DOCX/TXT text extractor
  backend/app/services/skills_taxonomy.py # In-memory taxonomy lookup
  backend/app/services/jd_parser.py       # Rule + spaCy JD parsing engine
  backend/app/main.py                     # Registered jd router & table creation
  backend/requirements.txt                # Added spacy, PyMuPDF, python-docx, pytest, httpx
  backend/scripts/generate_sample_files.py # Generates docx and pdf from sample texts
  backend/scripts/expand_taxonomy.py      # Taxonomy expansion script
  backend/tests/test_jd_parser.py         # 40 unit & parser tests
  backend/tests/test_jd_api.py            # 12 API endpoint integration tests

Frontend:
  frontend/src/api/jd.js                  # Axios client methods for JD API
  frontend/src/context/JDContext.jsx      # Global active JD context & hook
  frontend/src/components/SkillChips.jsx  # Editable chip list (remove/add/toggle)
  frontend/src/pages/Home.jsx             # Dual-tab input, analyze, results, edits
  frontend/src/main.jsx                   # Wrapped in JDProvider

Sample Data:
  sample_data/jds/java_backend_jd.txt     # Java / Spring Boot JD (TXT)
  sample_data/jds/react_frontend_jd.txt   # React Frontend JD (TXT source)
  sample_data/jds/react_frontend_jd.docx  # React Frontend JD (DOCX format)
  sample_data/jds/aiml_engineer_jd.txt    # AI/ML Engineer JD (TXT source)
  sample_data/jds/aiml_engineer_jd.pdf    # AI/ML Engineer JD (PDF format)
```

### Test Results

| Test Suite | Total Tests | Passed | Result |
|------------|-------------|--------|--------|
| `test_jd_parser.py` (Parser & NLP) | 40 | 40 | ✅ 100% Pass |
| `test_jd_api.py` (FastAPI REST API) | 12 | 12 | ✅ 100% Pass |
| **Total Test Suite** | **52** | **52** | **✅ 100% Pass** |
| `vite build` (Frontend SPA) | 106 modules | 106 | ✅ 100% Pass (8.76s) |

### Known Issues

- None.

---

## Phase 2 — Resume Parsing
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
