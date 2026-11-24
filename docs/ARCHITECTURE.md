# System Architecture & Technical Design Specification

> End-to-end architectural blueprint, execution flowcharts, relational database schemas, and module responsibility mappings for the **AI-Based Resume Matching & Candidate Ranking System**.

---

## 1. High-Level System Architecture

The application adopts a decoupled, multi-tier client-server architecture. The frontend is a single-page application (SPA) built with React 18, Vite, and Tailwind CSS. The backend is a modular Python service powered by FastAPI, spaCy, PyMuPDF, and SentenceTransformers.

```mermaid
flowchart TD
    subgraph Client["Frontend Client (React 18 + Vite)"]
        UI_Home["Home Page (Upload & Quick Demo)"]
        UI_Dash["Dashboard (Ranking Table & Filters)"]
        UI_Detail["Candidate Detail (Explainable Breakdown)"]
        UI_Boundary["Error Boundary & WCAG AA Layer"]
    end

    subgraph API_Gateway["FastAPI Gateway (Port 8080)"]
        CORS["CORS & Request Middleware"]
        R_Demo["/api/demo (One-Click Seeder)"]
        R_JD["/api/jd (Parse & Recruiter Edits)"]
        R_Resumes["/api/resumes (Batch Ingestion & Deletion)"]
        R_Match["/api/match (Execute & Config)"]
    end

    subgraph Parsing_Engine["Module 1 & 2: Parsing & Ingestion"]
        TE["text_extractor.py (PyMuPDF & python-docx)"]
        JDP["jd_parser.py (Section Segmentation & Requirements)"]
        RP["resume_parser.py (spaCy NER & Date Range Engine)"]
        TAX["skills_taxonomy.py (420+ Concepts & Parent Aliases)"]
    end

    subgraph Core_Engine["Module 3: Deterministic Matching Engine"]
        ME["matching_engine.py (5-Factor Weighted Aggregation)"]
        SKILL_EVAL["Skill Matching & Family Collapse"]
        SEM_EVAL["Semantic Duty Alignment (Dense Embeddings)"]
        EXP_EVAL["Domain Experience Ratio Engine"]
        KO_GUARD["Knockout Safeguard & Band Enforcer"]
        EMB["embedding_service.py (all-MiniLM-L6-v2 + SHA-1 Cache)"]
    end

    subgraph Storage_Layer["Module 4: Persistence & Database"]
        DB[(SQLite / PostgreSQL)]
        T_JD["job_descriptions"]
        T_CAND["candidates"]
        T_RUN["match_runs (Audit Snapshots)"]
        T_RES["match_results (Explainability Payloads)"]
    end

    %% Connections
    UI_Home -->|Upload Files / Seed Demo| API_Gateway
    UI_Dash -->|Query Leaderboard & Filters| R_Match
    UI_Detail -->|Fetch Audit Explainability| R_Match

    API_Gateway --> Parsing_Engine
    Parsing_Engine --> Core_Engine
    Core_Engine --> Storage_Layer
    EMB -.->|In-Memory Cache| Core_Engine
    Storage_Layer -->|Persisted Snapshots| API_Gateway
```

---

## 2. End-to-End Execution Sequence Flow

The diagram below illustrates the exact execution lifecycle from the moment a recruiter uploads files or clicks the one-click demo button to the final render of explainable candidate score cards.

```mermaid
sequenceDiagram
    autonumber
    actor Recruiter as Recruiter / Evaluator
    participant UI as Frontend SPA (React)
    participant API as FastAPI Router (/api/match)
    participant Parser as Ingestion & Parsers
    participant Taxonomy as Skills Taxonomy Graph
    participant Embed as Embedding Service
    participant Engine as Matching Engine
    participant DB as SQLite Database

    Recruiter->>UI: Selects Job Description & Resumes
    UI->>API: POST /api/demo/seed?jd=java (or manual upload)
    API->>Parser: extract_text() & segment sections
    Parser->>Taxonomy: Match skills against 420+ hierarchical concepts
    Parser->>Parser: Calculate verified experience tenure
    API->>DB: Store parsed JD and candidate records
    API->>Engine: rank(parsed_jd, candidates)
    
    rect rgb(240, 245, 235)
        note over Engine,Embed: Multi-Component Evaluation
        Engine->>Taxonomy: Collapse skill families & assign tiered credit (T1-T4)
        Engine->>Embed: Embed duty sentences & calculate cosine similarity matrix
        Engine->>Engine: Compute Domain Experience Ratio (Relevant vs Required)
        Engine->>Engine: Score Degree Level & Title Cosine Relevance
        Engine->>Engine: Apply Knockout Safeguard (Cap at 39% if skills < 25%)
    end

    Engine->>DB: Insert MatchRun snapshot & MatchResultDB rows
    DB-->>API: Match run ID & ranked payload
    API-->>UI: Return leaderboard JSON (< 20ms warm latency)
    UI-->>Recruiter: Renders Editorial Dashboard with WCAG AA badges
```

---

## 3. Relational Database Schema (Entity-Relationship Diagram)

The database schema is designed for immutable audit tracking, candidate privacy, and cascade deletion.

```mermaid
erDiagram
    JOB_DESCRIPTIONS ||--o{ MATCH_RUNS : "initiates"
    CANDIDATES ||--o{ MATCH_RESULTS : "evaluated in"
    MATCH_RUNS ||--|{ MATCH_RESULTS : "contains"

    JOB_DESCRIPTIONS {
        int id PK "Auto-increment"
        string title "Normalized Role Title"
        text raw_text "Original Uploaded Text"
        json parsed_json "Requirements, Skills & Qualifications"
        string source "'upload' or 'paste'"
        string filename "Source File Name"
        datetime created_at "UTC Timestamp"
        datetime updated_at "UTC Timestamp"
    }

    CANDIDATES {
        int id PK "Auto-increment"
        string filename "Uploaded Resume Filename"
        string name "Parsed Candidate Name"
        string email "Contact Email (Nullable)"
        string phone "Contact Phone (Nullable)"
        float total_experience_years "Verified Chronological Tenure"
        json parsed_json "Structured Skills, Roles & Education"
        text raw_text "Extracted Plain Text"
        datetime created_at "UTC Timestamp"
    }

    MATCH_RUNS {
        int id PK "Auto-increment"
        int jd_id FK "References job_descriptions.id (CASCADE)"
        string jd_snapshot_hash "SHA-256 Content Hash"
        int candidate_count "Cohort Size"
        float duration_ms "Execution Latency in Milliseconds"
        json config_snapshot "Active Scoring Weights & Thresholds"
        datetime created_at "UTC Execution Timestamp"
    }

    MATCH_RESULTS {
        int id PK "Auto-increment"
        int run_id FK "References match_runs.id (CASCADE)"
        int candidate_id FK "References candidates.id (CASCADE)"
        int rank "Position in Leaderboard (1 to N)"
        float final_score "Composite Match (0.0 to 100.0)"
        string band "'Strong', 'Good', 'Partial', 'Weak'"
        boolean is_knockout "Knockout Safeguard Flag"
        json result_json "Itemized Component Breakdown & Evidence"
        datetime created_at "UTC Timestamp"
    }
```

---

## 4. Codebase Module & File Responsibility Mapping

The table below maps the functional responsibilities of every core module across the repository:

| Module | File Path | Primary Responsibilities |
| :--- | :--- | :--- |
| **Module 1: JD Parser** | [backend/app/services/jd_parser.py](file:///c:/Users/singh/OneDrive/Desktop/AI-Based%20Resume%20Matching%20%26%20Candidate%20Ranking%20System/backend/app/services/jd_parser.py) | Section segmentation, title extraction, required vs preferred skill isolation, experience range detection, degree classification, short JD warning generation. |
| **Module 2: Resume Parser** | [backend/app/services/resume_parser.py](file:///c:/Users/singh/OneDrive/Desktop/AI-Based%20Resume%20Matching%20%26%20Candidate%20Ranking%20System/backend/app/services/resume_parser.py) | Layout extraction, spaCy PERSON NER, contact heuristics, chronological interval union algorithm, stated experience capture, education degree mapping. |
| **Module 2b: Text Extractor** | [backend/app/services/text_extractor.py](file:///c:/Users/singh/OneDrive/Desktop/AI-Based%20Resume%20Matching%20%26%20Candidate%20Ranking%20System/backend/app/services/text_extractor.py) | PyMuPDF two-column layout detection, python-docx table & header extraction, Scanned PDF error detection, unicode ligature & date symbol normalization. |
| **Module 2c: Skills Taxonomy** | [backend/app/services/skills_taxonomy.py](file:///c:/Users/singh/OneDrive/Desktop/AI-Based%20Resume%20Matching%20%26%20Candidate%20Ranking%20System/backend/app/services/skills_taxonomy.py) | In-memory indexing of 420+ concept graph, synonym aliasing, parent concept resolution, and skill family lookups. |
| **Module 3: Matching Engine** | [backend/app/services/matching_engine.py](file:///c:/Users/singh/OneDrive/Desktop/AI-Based%20Resume%20Matching%20%26%20Candidate%20Ranking%20System/backend/app/services/matching_engine.py) | Multi-factor weighted composite scoring, Tier 1–4 skill credit, family collapse, semantic duty matrix cosine dot products, Knockout Safeguard enforcement. |
| **Module 3b: Embedding Service**| [backend/app/services/embedding_service.py](file:///c:/Users/singh/OneDrive/Desktop/AI-Based%20Resume%20Matching%20%26%20Candidate%20Ranking%20System/backend/app/services/embedding_service.py) | `all-MiniLM-L6-v2` SentenceTransformer wrapper, SHA-1 string cache, offline-first fallback, and cosine rescaling algorithms. |
| **Module 4: API & Persistence**| [backend/app/routers/](file:///c:/Users/singh/OneDrive/Desktop/AI-Based%20Resume%20Matching%20%26%20Candidate%20Ranking%20System/backend/app/routers/) | REST endpoints (`/api/jd`, `/api/resumes`, `/api/match`, `/api/demo`), SQLite relational transaction management, cascade pruning, and staleness detection. |
| **Module 5: Frontend UI** | [frontend/src/](file:///c:/Users/singh/OneDrive/Desktop/AI-Based%20Resume%20Matching%20%26%20Candidate%20Ranking%20System/frontend/src/) | React 18 editorial dashboard, Tailwind CSS design tokens, WCAG AA compliance, Error Boundary, StatTiles, ScoreBars, and responsive views. |

---

## 5. Architectural Decisions Reference (DECISIONS.md Summary)

The system's development was guided by 59 formal Architectural Decisions recorded in [DECISIONS.md](file:///c:/Users/singh/OneDrive/Desktop/AI-Based%20Resume%20Matching%20%26%20Candidate%20Ranking%20System/DECISIONS.md). The critical architectural choices include:

- **D1, D3, D5:** Local sentence embeddings (`all-MiniLM-L6-v2`) and deterministic mathematical models over cloud generative LLMs for sub-20ms speed, zero API costs, and strict GDPR compliance.
- **D4:** SQLAlchemy ORM with SQLite file storage for single-command developer setup, designed with complete PostgreSQL migration portability.
- **D12:** Skill Family Collapse to neutralize resume keyword stuffing.
- **D18:** Knockout Safeguard capping candidates with $<25\%$ core skills at 39% ('Weak match').
- **D28:** Cascade deletion ensuring deletion of candidate records prunes all foreign key match entries.
- **D48 (superseding D43):** Calibrating job title cosine similarity bounds from $[0.15, 0.70]$ to $[0.30, 0.75]$, strictly preventing cross-domain marketing or non-technical roles from receiving unearned title scores.
- **D51:** Frontend band consistency rule establishing backend `/api/match/config` as the absolute single source of truth for all score bands and thresholds.
- **D59:** Responsible AI protocol excluding all demographic attributes (gender, age, photo, ethnicity) from candidate scoring pipelines.
