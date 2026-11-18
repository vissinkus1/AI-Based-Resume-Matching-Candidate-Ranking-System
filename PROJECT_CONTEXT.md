# PROJECT CONTEXT

> **This file is the permanent contract for the entire project.**
> Read it at the start of every session before writing any code.

## Project

**AI-Based Resume Matching & Candidate Ranking System**

Compares multiple resumes against one Job Description (JD) and ranks
candidates with an explainable 0–100 match score.

### Evaluation Criteria

| Weight | Criterion |
|--------|-----------|
| 25 % | Functional application |
| 15 % | Resume parsing accuracy |
| 25 % | JD-to-resume matching logic |
| 15 % | Matching score and explanation |
| 10 % | UI/UX and usability |
| 10 % | Code quality and documentation |

Working, well-reasoned, well-documented prototype — not a polished
production platform.  Every line and algorithm must be explainable in a
technical interview: prefer simple, readable, well-commented code.

---

## Required Features

| ID | Feature | Description |
|----|---------|-------------|
| M1 | JD input | Paste text or upload PDF/DOCX/TXT; extract skills, experience requirement, qualifications, key responsibilities. |
| M2 | Resume upload | Batch ≥ 10 at once, PDF + DOCX; extract name, email, phone, skills, total experience (years), education, job titles, summary. |
| M3 | Matching | Per resume: overall score 0–100, matched/missing skills, experience evaluation, **semantic** similarity (not only keyword). |
| M4 | Ranking dashboard | Table: Candidate · Experience · Match % · Matched Skills — sorted by score, with sorting/filtering. |
| M5 | Candidate detail | Extracted info, overall score, matched/missing skills, experience comparison, plain-English reasons, score breakdown. |

**Rule:** Only synthetic or publicly licensed sample resumes — never real personal data.

---

## Tech Stack (FIXED)

### Frontend
- React.js, Vite, **JavaScript** (no TypeScript), Tailwind CSS
- Axios, React Router

### Backend
- Python 3.11+, FastAPI, Uvicorn, Pydantic, python-multipart

### Document Processing
- PyMuPDF (`fitz`) for PDF
- `python-docx` for DOCX

### AI / NLP
- `sentence-transformers` (`all-MiniLM-L6-v2`)
- spaCy (`en_core_web_sm`)
- scikit-learn

### Database
- **Dev:** SQLite via SQLAlchemy
- `DATABASE_URL` env var → PostgreSQL-ready with zero business-logic changes

### Dev Tooling
- Git, GitHub-ready structure

### Repo Layout
```
/backend       – FastAPI application
/frontend      – React SPA
/sample_data   – synthetic resumes & JDs
/docs          – algorithm doc, architecture diagrams
```

---

## Scoring Design

```
final_score = 0.40 * skill_score
            + 0.25 * semantic_score
            + 0.20 * experience_score
            + 0.10 * qualification_score
            + 0.05 * title_relevance_score
```

| Component | How it is calculated |
|-----------|---------------------|
| **skill_score** | Required-skill coverage via normalized taxonomy with aliases (`js` = `javascript`) + embedding-based soft match for near-synonyms above threshold. Required skills weigh more than preferred. |
| **semantic_score** | Cosine similarity of JD embedding vs resume embedding (section/chunk-wise, aggregated), rescaled 0–100. |
| **experience_score** | Candidate years vs required years — full credit if met, proportional if below, small cap on over-qualification bonus. |
| **qualification_score** | Degree / education match. |
| **title_relevance_score** | Embedding similarity of past job titles to JD role title. |

Every component must produce a machine-generated **explanation** (reasons list).
Weights live in **one config file** for easy tuning and interview explanation.

---

## Working Protocol

1. Maintain `PROJECT_CONTEXT.md`, `PROGRESS.md`, `DECISIONS.md` in repo root.
2. At session start: read all three, state what is DONE / CURRENT / NEXT.
3. Work ONLY on the current phase.
4. Never duplicate existing files — extend instead.
5. At phase end: test → update docs → PHASE REPORT → STOP.
6. Ambiguity → make sensible choice → record in DECISIONS.md → continue.
7. No placeholder/fake logic, no hardcoded scores, no mock data in matching.
8. Code quality: type hints, docstrings, small functions, clear modules,
   error handling, up-to-date `requirements.txt`.

---

## Phase List

| # | Phase | Status |
|---|-------|--------|
| 0 | Setup & context files | IN PROGRESS |
| 1 | JD module | TODO |
| 2 | Resume parsing | TODO |
| 3 | Matching engine | TODO |
| 4 | API + DB integration | TODO |
| 5 | Ranking dashboard | TODO |
| 6 | Candidate detail view | TODO |
| 7 | Synthetic data + testing + fixes | TODO |
| 8 | README, algorithm doc, demo, polish | TODO |
