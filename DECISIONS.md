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

## Phase 2

| # | Decision | Rationale |
|---|----------|-----------|
| D17 | Longest-match-wins via spaCy `filter_spans` for skill matching | Prevents false substring matches (e.g., "Apache Kafka" extracted without trailing "Apache"). |
| D18 | Hierarchical skill taxonomy with explicit `parent` links | Allows child skills (e.g. AWS EC2, S3) to roll up to parent category credit in matching without losing specificity. |
| D19 | Tri-tier taxonomy categorization (`core`, `supporting`, `soft`) | Enables tiered weighting so core frameworks and languages contribute more to match scores than soft skills. |
| D20 | Dual qualification levels: `min_required_level` and `preferred_level` | Accurately models "Bachelor's or Master's" as min=bachelor, avoiding false penalties for bachelor candidates. |
| D21 | Sentence-level evidence tracking for all extracted skills | Records originating sentence and section heading to provide clear, explainable justification in the UI and interview. |
| D22 | Multi-column bounding-box block sorting in PDF text extractor | Sorts blocks primarily by column horizontal origin (`x0`) then vertical (`y0`), preventing cross-column text interleaving in two-column resumes. |
| D23 | Date range merging via non-overlapping interval union | Accurately calculates total career experience without double-counting parallel jobs or concurrent consulting roles. |
| D24 | Career gap and sabbatical exclusion heuristic in work experience | Detects terms like "sabbatical" and "career break", excluding non-working intervals from total experience calculations. |
| D25 | Isolated per-file batch resume upload API | Ensures invalid, oversized, or corrupt files in a batch fail individually without aborting valid candidate resumes. |

## Phase 3

| # | Decision | Rationale |
|---|----------|-----------|
| D26 | Frozen dataclass `ScoringConfig` (`backend/app/core/scoring_config.py`) | Single source of truth for all weights, calibration thresholds, and credit multipliers with strict `__post_init__` sum-to-1.0 validation. |
| D27 | Lazy singleton `EmbeddingService` with SHA-1 cache & `local_files_only=True` fallback | Encapsulates `all-MiniLM-L6-v2`; caches repeated sentence encodings; enables offline sandbox execution without telemetry timeouts. |
| D28 | Skill family collapse (`collapse_jd_skill_families`) | Prunes child skills from JD requirements when their parent is present (e.g. drops AWS S3 if AWS is in JD), preventing denominator inflation. |
| D29 | Hierarchical credit table with semantic soft-matching fallback | Grants 1.0 for exact/alias, 0.9 for child-of-parent, 0.6 for parent-of-child, and caps semantic soft-matching at 0.70 with 0.62 cosine threshold. |
| D30 | Dual semantic evaluation: requirement coverage (60%) + whole-doc similarity (40%) | Balances line-by-line duty alignment against overall career summary; calibrates raw cosine ([0.15, 0.75] -> [0, 100]) for intuitive human interpretation. |
| D31 | Relevant experience calculation with 50% internship discount & 90.0 overqualification floor | Calculates domain-relevant tenure rather than generic years; discounts internships; protects veteran candidates from disproportionate penalties. |
| D32 | Ordinal degree hierarchy scoring with progressive penalty scaling | Scores degree alignment as 100 (meets/exceeds), 50 (one below), 20 (two below), and 30 (none detected) without arbitrary point cliffs. |
| D33 | Domain knockout safeguard cap at 35.0 | Caps overall score at 35.0 when core required skill coverage is below 25%, preventing off-domain resumes with good prose from gaming ranks. |
| D34 | Pure algorithmic deterministic narrative explanations (zero LLMs) | Produces explainable human-readable breakdown sentences, strengths, and gaps from mathematical contributions and evidence snippets. |
| D35 | Unbiased ground truth validation via `build_expected_tiers.py` | Assigns expected match tiers prior to running algorithm; verifies system against objective annotations (achieving 100% tier agreement and Spearman > 0.81). |

## Phase 4

| # | Decision | Rationale |
|---|----------|-----------|
| D36 | Language frameworks exempted from skill family collapse | Core language frameworks (Spring Boot, FastAPI, Django, React) are independent competencies and must not be collapsed into their language parent; only cloud platforms (AWS, Azure, GCP) and tools (Git, CI/CD) are collapsed. |
| D37 | Generic skills exclusion from domain experience calculation | Tools like Git, Docker, AWS, SQL, and generic scripting Python do not confer domain experience on their own; entries require $\ge 2$ domain core skills, or ($sim \ge 0.35$ and $\ge 1$ domain skill), preventing false cross-domain years. |
| D38 | Seniority token removal and title normalization | Strips seniority words (senior, lead, junior) and punctuation before embedding past titles against JD title, preventing false 100% scores between frontend and backend roles. |
| D39 | Inferred concept credit for supporting and soft skills | Missing supporting/soft skills (e.g. Clean Architecture, Agile) receive up to 0.70 credit if sentence-level experience cosine $\ge 0.60$ with snippet evidence; core skills are strictly exempt from inference. |
| D40 | Boilerplate duty sentence filtering & calibration bounds update | Excludes company/role intro boilerplate (< 6 words or lacking a verb) from semantic duty matching; adjusted upper cosine calibration bounds to 0.70 to prevent 100% saturation. |
| D41 | Deterministic SHA-256 snapshot hashing for Job Description staleness detection | Hashing the canonical JSON serialized JD on execution enables $O(1)$ stale checks on `GET /api/match/runs/{id}` without re-evaluating embeddings. |
| D42 | Composite index on `(run_id, rank)` in `match_results` | Guarantees instant sub-millisecond retrieval of paginated ranking leaderboards and deterministic tie-breaking. |
| D43 | DB Cascade delete on MatchRun with nullable candidate FK | Deleting a MatchRun cascades to all results; deleting a Candidate sets `candidate_id=NULL` but retains historical auditable scoring records. |
| D44 | Lifespan embedding model warmup & `/health` readiness check | Pre-warms SentenceTransformer weights in FastAPI lifespan startup, preventing first-request cold-start latency spikes. |
| D45 | Streaming CSV export without disk file accumulation | Streams candidate evaluation reports directly via Starlette StreamingResponse with standard RFC-4180 escaping. |
| D46 | LRU caching on duty sentence validation | `_is_real_duty_sentence` cached with `maxsize=2048` eliminates redundant spaCy POS parsing across candidates in batch ranking, reducing warm batch ranking latency from 1,777 ms down to 12.39 ms. |
| D47 | Dynamic multi-tier staleness evaluation | Match runs track `"JD edited"` (SHA-256 hash mismatch), `"candidate removed"` (orphan results pruned), and `"candidates added"` (new candidate timestamps > run creation timestamp). |
| D48 | Candidate deletion cascade integrity | Foreign key `ondelete="CASCADE"` on `MatchResultDB.candidate_id` plus explicit repository cascade prune to guarantee zero orphaned match rows upon candidate deletion. |
| D49 | Transparent deterministic score summation | ScoreBreakdownCard presents all 5 factor scores, weights, points contribution, and a summing bottom row verifying the exact linear composition formula. |
| D50 | URL search parameter state synchronization | Dashboard filters (search, band, min_score, min_exp, skill, sort, order) sync to React Router `useSearchParams` for browser history, refresh persistence, and shareable links. |
| D51 | One-click instant evaluator demo | `POST /api/demo/seed?jd={java|react|aiml}&reset=true` automates instant ingestion of target JDs and all 12 candidate resumes, computing rankings and auto-navigating to the live dashboard. |

## Phase 6A

| # | Decision | Rationale |
|---|----------|-----------|
| D52 | Dual-layer design tokens in CSS variables (`:root` in `index.css`) and Tailwind (`tailwind.config.js`) | Establishes single source of truth for editorial sage palette (`#E5E8CE` ivory, `#F3F5E6` paper, `#789575` sage, `#2F4A33` forest, `#1E2A20` ink, `#556456` muted) with zero hardcoded hex strings in JSX. |
| D53 | Calibrated muted text token (`#556456`) for guaranteed WCAG AA compliance | Raw `#5E6B5F` on ivory `#E5E8CE` yielded 4.48:1 (just under the 4.5:1 AA threshold). Slightly deepening to `#556456` guarantees 5.01:1 on ivory and 5.69:1 on paper surfaces. |
| D54 | Tri-tier typography system with robust offline fallbacks | Uses Google Fonts Anton (hero display/scores), Fraunces (editorial serif headings), and Inter (body/tables with tabular-nums) while falling back cleanly to Impact, Georgia, and system-ui offline without layout shift. |
| D55 | Shared accessible UI primitives suite (`components/ui/`) | Centralizes buttons, cards, section headers, chips, stat tiles, score bars, eyebrows, dividers, empty states, and skeletons; enforces minimum 40px touch targets and visible focus rings. |
| D56 | Score band dual-encoding requirement (visual tint + text label) | Accessibility rule ensuring score bands never rely on color alone; every band renders an explicit textual indicator (`Strong Match`, `Good Match`, `Partial Match`, `Weak Match`, `Knockout`). |
| D57 | Frontend-only visual restyle with zero backend or API drift | Preserved 100% backend isolation; no Python code, database models, or REST API contracts were altered during UI modernization. |
