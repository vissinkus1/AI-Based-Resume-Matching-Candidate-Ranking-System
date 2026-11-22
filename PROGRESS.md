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
**Status:** ✅ DONE

### Checklist

- [x] **Phase 1 Enhancements (Part A):**
  - [x] A1: Longest-match-wins implemented via `filter_spans` in `jd_parser.py` and `resume_parser.py`. Standalone "Apache" removed in favor of "Apache HTTP Server".
  - [x] A2: Hierarchical skills taxonomy with `parent` tracking (e.g., AWS EC2/S3/Lambda -> AWS, GitHub -> Git) across 327 skills.
  - [x] A3: Tri-tier skill classification (`core`, `supporting`, `soft`) added to taxonomy and schema.
  - [x] A4: Normalized dual qualification levels (`min_required_level` and `preferred_level`) extracted from JDs.
  - [x] A5: Sentence-level evidence tracking (`skill_evidence`) mapping every extracted skill to its section and sentence; verified via `backend/scripts/debug_jd.py`.
- [x] **Resume Parser Service (Part B1):**
  - [x] `backend/app/services/resume_parser.py`: Multi-format date extraction, non-overlapping date interval merger with injectable `today`, education degree/level normalization, candidate contact extraction (email, phone, socials, location), and section segmentation.
  - [x] Multi-column PDF reading-order preservation in `backend/app/services/text_extractor.py` (sorting blocks by `x0` then `y0`).
- [x] **Database & Repositories (Part B2):**
  - [x] SQLAlchemy model `Candidate` in `backend/app/models/candidate.py` (columns: `id`, `filename`, `name`, `email`, `phone`, `total_experience_years`, `parsed_json`, `raw_text`, `created_at`).
  - [x] `CandidateRepository` in `backend/app/repositories/candidate_repository.py` with CRUD, listing, deletion, and bulk clear.
  - [x] Pydantic schemas in `backend/app/schemas/candidate.py` (`CandidateResponse`, `CandidateListItem`, `SingleUploadResult`, `BatchUploadResponse`).
- [x] **Batch Intake & Candidate Management API (Part B3):**
  - [x] `POST /api/resumes/upload`: Up to 50 files, 5 MB limit, PDF/DOCX only, independent file error isolation.
  - [x] `GET /api/resumes`: Candidate listing with top 5 skills and warning counts.
  - [x] `GET /api/resumes/{id}`: Detailed parsed candidate view.
  - [x] `DELETE /api/resumes/{id}` and `DELETE /api/resumes`: Individual deletion and bulk clearing.
- [x] **Frontend Resume Intake UI (Part B4):**
  - [x] Step 2 multi-file drag-and-drop zone on `frontend/src/pages/Home.jsx`.
  - [x] Selected files staging list with file count recommendation (10+).
  - [x] Upload progress bar and per-file status badges.
  - [x] Interactive parsed candidates table (Name, Email/Phone, Experience, Top Skills, Warnings, Delete).
  - [x] Step 1 active JD persistent indicator and "Run Matching" callout banner.
- [x] **Synthetic Evaluation Dataset & Ground Truth (Part B5):**
  - [x] Generator script `backend/scripts/generate_sample_resumes.py` creating 12 synthetic resumes (7 PDF, 5 DOCX) in `sample_data/resumes/`.
  - [x] Diverse test cases: two-column layout, contact tables, non-standard dates ("Jun'19", "Since 2022"), fresher (0 yrs), overlapping jobs, career break sabbatical, 9.5y senior, digital marketer negative example.
  - [x] Ground truth dataset `sample_data/resumes/ground_truth.json`.
  - [x] Benchmark script `backend/scripts/evaluate_parsing.py` achieving **96.2% overall accuracy** (all categories >= 85%).
- [x] **Automated Test Suite (Part B6):**
  - [x] 18 unit tests in `backend/tests/test_resume_parser.py`.
  - [x] 9 API integration tests in `backend/tests/test_resumes_api.py`.
  - [x] Full test suite (83 tests) passing with 100% pass rate.

### Files Created / Modified

```
Backend:
  backend/app/models/candidate.py              # Candidate SQLAlchemy ORM model
  backend/app/models/__init__.py               # Export Candidate
  backend/app/repositories/candidate_repository.py # Candidate CRUD operations
  backend/app/repositories/__init__.py         # Export CandidateRepository
  backend/app/schemas/candidate.py             # Pydantic schemas for candidate intake
  backend/app/schemas/jd.py                    # Added min_required_level, preferred_level, skill_evidence
  backend/app/services/text_extractor.py       # Two-column PDF block sorting
  backend/app/services/skills_taxonomy.py      # Parent tracking and tri-tier taxonomy loading
  backend/app/services/jd_parser.py            # Longest-match-wins, qualification levels, evidence
  backend/app/services/resume_parser.py        # Comprehensive resume parsing service
  backend/app/routers/resumes.py               # Batch upload & candidate management endpoints
  backend/app/routers/__init__.py              # Export resumes router
  backend/app/main.py                          # Register candidate model & resumes router
  backend/app/data/skills_taxonomy.json        # 327 skills with parent and tier attributes
  backend/scripts/generate_sample_resumes.py   # Generates 12 synthetic PDF/DOCX resumes
  backend/scripts/evaluate_parsing.py          # Benchmark evaluation script
  backend/scripts/debug_jd.py                  # JD parsing & evidence verification script
  backend/tests/test_resume_parser.py          # 18 unit tests for resume parsing
  backend/tests/test_resumes_api.py            # 9 API integration tests for resume upload
  backend/tests/test_jd_parser.py              # 44 JD parser tests (including A1-A5 checks)

Frontend:
  frontend/src/api/resumes.js                  # Axios client for /api/resumes endpoints
  frontend/src/pages/Home.jsx                  # Batch dropzone, progress bar, parsed candidate table

Sample Data:
  sample_data/resumes/candidate_01_aravind_sharma_java.pdf
  sample_data/resumes/candidate_02_priya_patel_react.docx
  sample_data/resumes/candidate_03_rohit_verma_aiml.pdf
  sample_data/resumes/candidate_04_ananya_iyer_fullstack.docx
  sample_data/resumes/candidate_05_deepak_nair_fresher.pdf
  sample_data/resumes/candidate_06_vikram_singh_overlap.docx
  sample_data/resumes/candidate_07_meera_deshmukh_gap.pdf
  sample_data/resumes/candidate_08_siddharth_reddy_senior.docx
  sample_data/resumes/candidate_09_kavita_krishnan_data_nlp.pdf
  sample_data/resumes/candidate_10_pooja_hegde_marketer.docx
  sample_data/resumes/candidate_11_rahul_kapoor_devops.pdf
  sample_data/resumes/candidate_12_sneha_banerjee_react_java.pdf
  sample_data/resumes/ground_truth.json        # Ground truth annotations
```

### Test Results

| Test Suite | Total Tests | Passed | Result |
|------------|-------------|--------|--------|
| `test_jd_parser.py` (JD Parsing & NLP) | 44 | 44 | ✅ 100% Pass |
| `test_jd_api.py` (JD REST API) | 12 | 12 | ✅ 100% Pass |
| `test_resume_parser.py` (Resume Parsing) | 18 | 18 | ✅ 100% Pass |
| `test_resumes_api.py` (Resumes REST API) | 9 | 9 | ✅ 100% Pass |
| **Total Automated Tests** | **83** | **83** | **✅ 100% Pass** |
| `evaluate_parsing.py` (Ground Truth Benchmark) | 12 Resumes | 12 | **✅ 96.2% Accuracy** |
| `vite build` (Frontend SPA) | 107 modules | 107 | ✅ 100% Pass (9.16s) |

### Benchmark Evaluation Summary

| Metric | Target | Measured | Result |
|--------|--------|----------|--------|
| Name Extraction Accuracy | >= 85% | **100.0%** | ✅ PASS |
| Email Extraction Accuracy | >= 85% | **100.0%** | ✅ PASS |
| Phone Extraction Accuracy | >= 85% | **100.0%** | ✅ PASS |
| Experience Accuracy (within ±0.5 yr) | >= 85% | **100.0%** | ✅ PASS |
| Education Level Accuracy | >= 85% | **100.0%** | ✅ PASS |
| Skill Recall | >= 85% | **87.7%** | ✅ PASS |
| Skill Precision | — | **69.3%** | Informational |
| **Overall System Accuracy** | **>= 85%** | **96.2%** | **✅ PASS** |

### Known Issues & Mitigations

- **Skill Precision (69.3%):** Taxonomy phrase matching picks up foundational skills mentioned in project descriptions and course titles beyond strict core competencies. This is addressed in Phase 3 where skills are weighted by tier (`core`, `supporting`, `soft`) and section confidence (`strong`, `medium`, `basic`).
- **Two-Column PDF OCR/Rendering:** If a PDF has unstructured non-standard text column coordinates with overlapping bounding boxes, block-sorting by `x0` column groups handles standard layouts cleanly. Unusual multi-grid resumes may trigger a parse warning.

---

## Phase 3 — Matching Engine
**Status:** ✅ DONE

### Checklist

- [x] Small parser fixes:
  - [x] Clean job titles (`_clean_job_title_and_company`) stripping company/location across ` | `, ` - `, ` at `, ` @ `, `,`
  - [x] Work experience description field and embedded taxonomy skills detection (`skills_in_entry`)
  - [x] Zero regressions on parsing benchmarks (maintained 96.2% overall system accuracy)
- [x] Scoring config (`backend/app/core/scoring_config.py`):
  - [x] Frozen dataclass with all weights, thresholds, calibration bounds, and credit tables
  - [x] Strict `__post_init__` sum-to-1.0 assertion
- [x] Embedding service (`backend/app/services/embedding_service.py`):
  - [x] Singleton wrapper for `all-MiniLM-L6-v2` with `local_files_only=True` offline fallback
  - [x] Batch encoding with L2 normalization
  - [x] In-memory SHA-1 text cache
  - [x] Fast vectorized cosine similarity matrix & linear calibration ([0.15, 0.75] -> [0, 100])
- [x] Matching engine (`backend/app/services/matching_engine.py`):
  - [x] Skill family collapse (`collapse_jd_skill_families`)
  - [x] Multi-tier credit table: exact/alias 1.0, child-of-parent 0.9, parent-of-child 0.6, semantic soft match <= 0.70
  - [x] Dual semantic evaluation: requirement-unit coverage (60%) + whole-doc cosine (40%)
  - [x] Relevant experience scoring with 50% internship discount and 90.0 overqualification floor
  - [x] Progressive degree ranking (100, 50, 20, 30)
  - [x] Past job title relevance matching (with summary fallback)
  - [x] Knockout safeguard cap at 35.0 when core skill coverage < 25%
  - [x] Deterministic plain-English narrative explanation generator (zero LLM calls)
  - [x] Fast batch candidate ranking with deterministic tie-breaking
- [x] Verification scripts & testing:
  - [x] Unbiased ground-truth generator (`backend/scripts/build_expected_tiers.py` -> `sample_data/expected_tiers.json`)
  - [x] Comprehensive evaluation runner (`backend/scripts/run_matching.py`)
  - [x] Keyword vs Semantic vs Hybrid ablation study
  - [x] 18 automated matching unit and integration tests (`backend/tests/test_matching_engine.py`)
  - [x] Full test suite execution (104 tests passing, 100% pass rate)
  - [x] Algorithm documentation (`docs/ALGORITHM.md`)

### Files Created & Modified

```
Backend:
  backend/app/core/scoring_config.py           # Frozen dataclass with all algorithm weights & parameters
  backend/app/services/embedding_service.py    # Lazy singleton SentenceTransformer with SHA-1 cache
  backend/app/services/matching_engine.py      # Core explainable matching & ranking engine
  backend/app/services/resume_parser.py        # Added title cleaning, description extraction, and skills_in_entry
  backend/app/schemas/candidate.py             # Added description & skills_in_entry to ExperienceEntrySchema
  backend/scripts/build_expected_tiers.py      # Pre-evaluation ground truth tier generator
  backend/scripts/run_matching.py              # Verification runner across 3 JDs with ablation study
  backend/tests/test_matching_engine.py        # 18 comprehensive tests covering credit table, knockout, determinism
  backend/tests/test_resume_parser.py          # Added A1 & A2 parser fix tests (21 total tests)

Documentation:
  docs/ALGORITHM.md                            # Comprehensive math formula, component weights & interview walkthrough
  sample_data/expected_tiers.json              # Unbiased ground-truth match tier targets
```

### Test Results

| Test Suite | Total Tests | Passed | Result |
|------------|-------------|--------|--------|
| `test_jd_parser.py` (JD Parsing & NLP) | 44 | 44 | ✅ 100% Pass |
| `test_jd_api.py` (JD REST API) | 12 | 12 | ✅ 100% Pass |
| `test_resume_parser.py` (Resume Parsing) | 21 | 21 | ✅ 100% Pass |
| `test_resumes_api.py` (Resumes REST API) | 9 | 9 | ✅ 100% Pass |
| `test_matching_engine.py` (Matching Engine) | 18 | 18 | ✅ 100% Pass |
| **Total Automated Tests** | **104** | **104** | **✅ 100% Pass** |
| `evaluate_parsing.py` (Resume Parsing Accuracy) | 12 Resumes | 12 | **✅ 96.2% Accuracy** |

### Matching Engine Performance & Evaluation Metrics

| Job Description | Candidates | Match Latency | Tier Agreement | Spearman Rank Correlation |
|-----------------|------------|---------------|----------------|--------------------------|
| **Java/Spring Boot Backend** | 12 resumes | 1229.6 ms (warm) | **100.0%** | **+0.909** |
| **React Frontend Developer** | 12 resumes | 88.8 ms (~7.4 ms/res) | **100.0%** | **+0.965** |
| **AI/ML Engineer** | 12 resumes | 104.4 ms (~8.7 ms/res) | **100.0%** | **+0.818** |

### Known Issues & Mitigations

- **Initial Cold-Start Embedding Initialization:** Loading PyTorch DLLs and `all-MiniLM-L6-v2` takes ~9.5 s on cold process launch. Mitigated by using lazy singleton loading so subsequent batch ranking takes under 100 ms total across 12 candidates (< 10 ms per candidate).
- **HuggingFace Network Telemetry on Windows:** In isolated sandbox environments, unconfigured `SentenceTransformer` attempted online commit hash lookups. Mitigated by setting `local_files_only=True` first, guaranteeing instantaneous local offline loads from disk cache.

## Phase 4 — API + DB Integration

**Status:** ✅ DONE

### Checklist

- [x] Part A: Matching Engine Fixes (verified with 9 dedicated unit tests):
  - [x] A1: Skill integrity & family collapse fix (`Java` and `Spring Boot` preserved; strictly separated `matched_required`, `matched_preferred`, `missing_required`, `missing_preferred`; required-only narrative counts)
  - [x] A2: Relevant experience generic skills exclusion (`GENERIC_SKILLS` defined; requires $\ge 2$ domain core skills, or $sim \ge 0.35$ with $\ge 1$ domain core skill)
  - [x] A3: Title normalization stripping seniority tokens (`senior`, `lead`, `junior`, `principal`, etc.) and punctuation before embedding
  - [x] A4: Inferred concept credit for supporting/soft skills (sentence-level experience cosine $\ge 0.60$, up to 0.70 credit; core tier strictly excluded)
  - [x] A5: Boilerplate duty sentence filtering ($\ge 6$ words + verb required) and polished narrative explanations without "including none"
  - [x] A6: Matched skills sorted by tier (core first), credit descending, and alphabetical; added `matched_top` (up to 6)
  - [x] A7: Calibrated cosine upper bounds raised to 0.70 preventing 100% score saturation
- [x] Part B: Database Integration:
  - [x] `MatchRun` model (`id`, `jd_id`, `jd_snapshot_hash`, `candidate_count`, `duration_ms`, `config_snapshot`, `created_at`)
  - [x] `MatchResultDB` model (`id`, `run_id`, `candidate_id`, `rank`, `final_score`, `band`, `is_knockout`, `result_json`, `created_at`) with composite index on `(run_id, rank)`
  - [x] Cascade deletion configured for runs; candidates set null on delete to preserve scoring audit trail; SQLite foreign keys enabled via connection listener
  - [x] `MatchRepository` with `create_run`, `get_run`, `list_runs`, `get_run_results`, `get_candidate_result`, `delete_run`, and `compute_jd_hash`
  - [x] Real-time JD staleness detection comparing stored SHA-256 snapshot hash to current JD content
- [x] Part C: REST API Endpoints under `/api/match`:
  - [x] `POST /api/match/run` (triggers matching run with timing and persistence)
  - [x] `GET /api/match/runs` (lists historical runs with `is_stale` flag)
  - [x] `GET /api/match/runs/{run_id}` (detailed summary, distribution across bands, and top candidate)
  - [x] `GET /api/match/runs/{run_id}/results` (paginated results with sorting by rank/final_score/created_at, band filter, min_score filter)
  - [x] `GET /api/match/runs/{run_id}/results/{candidate_id}` (exhaustive candidate explainable breakdown)
  - [x] `GET /api/match/runs/{run_id}/export.csv` (RFC-4180 streaming CSV export)
  - [x] `DELETE /api/match/runs/{run_id}` (deletes run and cascade cleans up results)
  - [x] `GET /api/match/config` (exposes active scoring weights, tiers, thresholds)
  - [x] Lifespan embedding model pre-warming during FastAPI startup; `/health` reports `model_ready: True`
- [x] Part D: Frontend Wiring:
  - [x] `frontend/src/api/match.js` Axios API client methods
  - [x] Interactive "Run AI Matching & Ranking" button in `Home.jsx` with spinner and auto-navigation to `/dashboard?run=<id>`
  - [x] Verification list and run selector in `Dashboard.jsx` (summary cards, staleness alert, ranking table, knockout badges, CSV download)
  - [x] Vite production build verified passing (108 modules, 0 errors)
- [x] Part E: Verification & Testing:
  - [x] Pytest suite `backend/tests/test_match_api.py` (9 tests covering health, config, runs, pagination, staleness, CSV, cascade deletes)
  - [x] End-to-end API smoke test script `backend/scripts/api_smoke_test.py` (10 steps end-to-end against live endpoints)
  - [x] 122 automated pytest tests passing across all suites (100% pass rate)

### Files Created & Modified

```
Backend Models & Repository:
  backend/app/models/match.py                  # MatchRun and MatchResultDB ORM models
  backend/app/models/__init__.py               # Exported MatchRun & MatchResultDB
  backend/app/repositories/match_repository.py # MatchRepository data access layer + compute_jd_hash
  backend/app/repositories/__init__.py         # Exported MatchRepository & compute_jd_hash
  backend/app/db/database.py                   # Added SQLite PRAGMA foreign_keys=ON listener

Backend API & Services:
  backend/app/schemas/match.py                 # Pydantic request/response schemas for match runs & results
  backend/app/schemas/__init__.py              # Exported match schemas
  backend/app/services/match_service.py        # MatchService orchestrator hydrating ORM models to ParsedJD/Resume
  backend/app/services/embedding_service.py    # Added warmup() and is_ready() methods
  backend/app/routers/match.py                 # REST API endpoints (/api/match/*)
  backend/app/routers/health.py                # Updated /health to report model_ready
  backend/app/routers/__init__.py              # Exported match router
  backend/app/main.py                          # Lifespan embedding warmup + registered match router

Frontend:
  frontend/src/api/match.js                    # Axios client for matching API
  frontend/src/pages/Home.jsx                  # Wired "Run AI Matching" button and navigation
  frontend/src/pages/Dashboard.jsx             # Added run query param reading, summary stats, verification list, CSV export

Verification & Tests:
  backend/tests/test_match_api.py              # 9 API integration tests
  backend/tests/test_matching_fixes_phase4.py  # 9 matching fix unit tests (A1-A7)
  backend/scripts/api_smoke_test.py            # 10-step end-to-end smoke test script
```

### Test Results Summary

| Test Suite | Total Tests | Passed | Result |
|------------|-------------|--------|--------|
| `test_jd_parser.py` (JD Parsing & NLP) | 44 | 44 | ✅ 100% Pass |
| `test_jd_api.py` (JD REST API) | 12 | 12 | ✅ 100% Pass |
| `test_resume_parser.py` (Resume Parsing) | 21 | 21 | ✅ 100% Pass |
| `test_resumes_api.py` (Resumes REST API) | 9 | 9 | ✅ 100% Pass |
| `test_matching_engine.py` (Matching Engine) | 18 | 18 | ✅ 100% Pass |
| `test_matching_fixes_phase4.py` (Phase 4 Fixes A1-A7) | 9 | 9 | ✅ 100% Pass |
| `test_match_api.py` (Matching REST API) | 9 | 9 | ✅ 100% Pass |
| **Total Automated Pytest Suite** | **122** | **122** | **✅ 100% Pass** |
| `api_smoke_test.py` (End-to-End API Smoke Test) | 10 Steps | 10 | **✅ 100% Pass** |
| `evaluate_parsing.py` (Resume Parsing Accuracy) | 12 Resumes | 12 | **✅ 96.2% Accuracy** |

### Benchmark Evaluation Metrics Across 3 Target JDs

| Target Job Description | Cohort | Match Latency | Tier Agreement | Spearman Rank Correlation |
|------------------------|--------|---------------|----------------|--------------------------|
| **Java/Spring Boot Backend** | 12 resumes | 3144.9 ms (cold) / 88 ms (warm) | **100.0%** | **+0.916** |
| **React Frontend Developer** | 12 resumes | 1730.0 ms | **100.0%** | **+0.972** |
| **AI/ML Engineer** | 12 resumes | 2128.0 ms | **100.0%** | **+0.832** |

## Phase 5 — Ranking Dashboard
**Status:** TODO

## Phase 6 — Candidate Detail View
**Status:** TODO

## Phase 7 — Synthetic Data + Testing + Fixes
**Status:** TODO

## Phase 8 — README, Algorithm Doc, Demo, Polish
**Status:** TODO
