# JADWA (جدوى) — AI Feasibility Study Platform

## What This Project Is

JADWA is an Arabic-first AI-powered SaaS that generates professional feasibility studies for the Saudi Arabian market. Users submit business intake data, and a 15-agent pipeline (powered by Claude API) produces bilingual (Arabic/English) PDF reports with financial modeling, market analysis, legal compliance, and Vision 2030 alignment.

**Target users:** Saudi entrepreneurs, SMEs, and consultants who need data-driven feasibility studies.

## Architecture Overview

```
┌─────────────┐     ┌──────────────┐     ┌──────────┐     ┌───────┐
│  Next.js     │────▶│  FastAPI      │────▶│  Celery   │────▶│ Claude │
│  Frontend    │     │  REST API     │     │  Workers  │     │  API   │
│  :3000       │     │  :8000        │     │  (15 agents)    │        │
└─────────────┘     └──────┬───────┘     └────┬─────┘     └───────┘
                           │                   │
                    ┌──────┴───────┐    ┌──────┴─────┐
                    │  PostgreSQL  │    │   Redis     │
                    │  :5432       │    │   :6379     │
                    └──────────────┘    └────────────┘
```

### Key Directories

- `backend/app/agents/` — 15 AI agents, all inherit from `BaseAgent`
- `backend/app/api/v1/` — FastAPI route handlers (auth, projects, reports)
- `backend/app/models/` — SQLAlchemy models (User, Project, ReportRun, etc.)
- `backend/app/core/` — Config, database, security, dependencies
- `backend/app/tasks/` — Celery app + DAG pipeline orchestration
- `backend/app/pdf/` — PDF templates and assets (WeasyPrint)
- `data-seed/` — Pre-loaded Saudi business data (GASTAT, SAMA, RFTA, HRDF, MCI, Vision2030)
- `frontend/` — Next.js app (early stage)

## Development Setup

### Prerequisites
- Python 3.11+, Node.js 20+, Docker (for PostgreSQL + Redis)

### Quick Start
```bash
# Start databases
docker compose up postgres redis -d

# Backend
cd backend && python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Fill in ANTHROPIC_API_KEY
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Celery worker (separate terminal)
cd backend && source venv/bin/activate
celery -A app.tasks.celery_app worker --loglevel=info --concurrency=4

# Frontend
cd frontend && npm install && npm run dev
```

### Environment Variables
Required in `backend/.env`:
```
ANTHROPIC_API_KEY=sk-ant-...
DATABASE_URL=postgresql://jadwa:jadwa_dev_pass@localhost:5432/jadwa
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=<random-32-chars>
```

## Agent Pipeline (Execution Order)

The report generation runs as a Celery task with a DAG of 15 agents:

| Tier | Agents | Parallelism |
|------|--------|-------------|
| 1 | IntakeValidation → SectorRouter | Sequential |
| 2 | Market + Legal + HR + [Franchise\|RealEstate] | Parallel (4 workers) |
| 2b | Financial + Competitive (needs Tier 2) | Parallel (2 workers) |
| 2c | Vision2030 + Risk (needs all Tier 2) | Parallel (2 workers) |
| 3 | Charts → Compiler → QualityReview → PDF | Sequential |

Pipeline entry point: `backend/app/tasks/pipeline.py:run_report_pipeline`
Base agent class: `backend/app/agents/base_agent.py:BaseAgent`

## Coding Conventions

### Python (Backend)
- **Framework:** FastAPI with async where beneficial, sync SQLAlchemy sessions
- **Models:** SQLAlchemy declarative with UUID primary keys
- **Agent pattern:** Inherit `BaseAgent`, implement `system_prompt` property and optionally `tools`/`execute_tool`
- **Config:** `pydantic-settings` with `.env` file loading
- **Auth:** JWT tokens via `python-jose`, passwords hashed with `bcrypt`
- **Imports:** Group stdlib, third-party, local. Use relative imports within `app/`
- **Types:** Use type hints on function signatures
- **Arabic strings:** Always use `ensure_ascii=False` in JSON serialization

### Frontend (Next.js)
- TypeScript preferred
- NextAuth.js for auth
- API calls go to FastAPI backend at `NEXT_PUBLIC_API_URL`

### Database
- All IDs are UUIDs (`uuid.uuid4()`)
- Use Alembic for migrations in production (currently using `create_all` for dev)
- JSONB columns for flexible data (intake_data, pipeline_state, etc.)

## Saudi Domain Knowledge

Key constants used throughout:
- **VAT:** 15% (applied to most sectors)
- **Zakat:** 2.5% (Islamic tax on net worth)
- **SAMA SAIBOR rate:** 5.95%
- **SIDF loan rate:** 3.5% (concessional lending)
- **Nitaqat bands:** Sector-specific Saudization ratios (see `data-seed/hrdf_nitaqat_ratios.json`)
- **Sectors:** retail, fnb, healthcare, education, technology, real_estate, manufacturing, logistics, hospitality, franchise, consulting, construction, agriculture, energy, finance

Regulatory bodies: SFDA (food), REGA (real estate), RFTA (franchise), MOH (health), MOE (education), CITC (tech), SAMA (finance)

## Testing

```bash
cd backend
pytest                           # Run all tests
pytest tests/agents/             # Agent tests only
pytest -x --tb=short             # Stop on first failure
```

## Common Tasks

### Adding a new agent
1. Create `backend/app/agents/my_agent.py` inheriting `BaseAgent`
2. Implement `system_prompt` property with bilingual instructions
3. Add tools list and `execute_tool()` if the agent needs tool_use
4. Wire into pipeline in `backend/app/tasks/pipeline.py`
5. Add to appropriate tier (parallel or sequential)

### Adding an API endpoint
1. Add route in appropriate `backend/app/api/v1/*.py` file
2. Create Pydantic request/response schemas inline or in schemas file
3. Register router in `backend/app/main.py` if new file

### Adding a database model
1. Create model in `backend/app/models/`
2. Import in `backend/app/models/__init__.py`
3. Create Alembic migration: `cd backend && alembic revision --autogenerate -m "description"`

## Important Notes

- The frontend directory is early-stage — most UI work is still ahead
- PDF rendering uses WeasyPrint with Arabic text shaping (fpdf2 as fallback)
- All agent outputs are logged to `agent_logs` table with token counts
- Data seed files are mock/static — production would integrate live APIs (SAMA, GASTAT, etc.)
- Moyasar payment integration is stubbed — needs real API keys for testing
- Progress is streamed via SSE at `GET /api/v1/reports/{run_id}/stream`
