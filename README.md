# AI-Based Resume Matching & Candidate Ranking System

> Compare multiple resumes against a Job Description and rank candidates with
> explainable 0–100 match scores.

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ and pnpm

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
python run.py
```

Backend runs on **http://localhost:8000**.  
Health check: `GET /health`

### Frontend

```bash
cd frontend
pnpm install
pnpm run dev
```

Frontend runs on **http://localhost:5173**.

---

## Project Structure

```
├── backend/          # FastAPI application
├── frontend/         # React SPA (Vite + Tailwind)
├── sample_data/      # Synthetic resumes & JDs
├── docs/             # Algorithm doc, architecture diagrams
├── PROJECT_CONTEXT.md
├── PROGRESS.md
└── DECISIONS.md
```

## Documentation

- [Project Context](PROJECT_CONTEXT.md) — requirements, stack, scoring design
- [Progress](PROGRESS.md) — phase checklist and status
- [Decisions](DECISIONS.md) — technical decisions log

*Full README will be completed in Phase 8.*
