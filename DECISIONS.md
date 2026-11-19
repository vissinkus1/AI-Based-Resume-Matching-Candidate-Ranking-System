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

## Phase 1

| # | Decision | Rationale |
|---|----------|-----------|
| D10 | Shared text extraction service in `services/text_extractor.py` | Extracts PDF, DOCX (paragraphs + tables), and TXT with clean normalization; generic for reuse in Phase 2 for resumes. |
| D11 | Skills taxonomy in `data/skills_taxonomy.json` with 327 canonical skills and 700+ aliases | O(1) case-insensitive alias-to-canonical lookup across 12 domains; shared by JD parser, resume parser, and matching engine. |
| D12 | spaCy PhraseMatcher + custom whole-word boundary check (`_is_whole_word_match`) | Eliminates false-positive substring matches (e.g. "Java" inside "JavaScript") while preserving case-insensitive multi-word aliases. |
| D13 | Section-guided required vs. preferred skill classification with inline fallback | Context-aware categorization using section headings ("Requirements" vs "Nice to Have") and sentence cues. |
| D14 | Range-first experience extraction with English word-to-number mapping | Prioritizes ranges ("3-5 years", "three to five years") over single digits to capture both min and max years accurately. |
| D15 | Repository pattern (`JDRepository`) for database access | Decouples SQLAlchemy ORM from FastAPI routes; supports transparent PostgreSQL swap in Phase 4. |
| D16 | React `JDContext` for shared active JD state across views | Allows Home, Dashboard, and Candidate Detail pages to access current JD without prop drilling. |
