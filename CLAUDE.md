# CLAUDE.md - JADWA Codebase Guide

## Project Overview

JADWA (جدوى — "Feasibility") is an Arabic-first AI-powered SaaS platform for generating comprehensive Saudi Arabia business feasibility studies. It uses a 15-agent multi-tier pipeline orchestrated via Celery, powered by Claude AI.

## Tech Stack

- **Backend**: FastAPI 0.115.0 (Python 3.11)
- **Database**: PostgreSQL 16 + SQLAlchemy 2.0 + Alembic
- **Task Queue**: Celery 5.4 + Redis 7
- **AI**: Anthropic Claude API (claude-sonnet-4-6)
- **PDF**: WeasyPrint 62.3 + Jinja2 templates (Arabic RTL support)
- **Auth**: JWT (python-jose) + bcrypt
- **Storage**: S3-compatible (AWS/MinIO/Cloudflare R2)
- **Payments**: Moyasar (Saudi payment gateway)
- **Frontend**: Next.js (planned, `/frontend` currently empty)
- **Infra**: Docker Compose (PostgreSQL, Redis, FastAPI, Celery worker)

## Directory Structure

```
backend/
├── app/
│   ├── main.py                  # FastAPI entry point
│   ├── core/
│   │   ├── config.py            # Pydantic settings (env vars)
│   │   ├── database.py          # SQLAlchemy engine + sessions
│   │   ├── security.py          # JWT + bcrypt utilities
│   │   └── deps.py              # OAuth2 dependencies
│   ├── models/                  # SQLAlchemy models
│   │   ├── user.py              # User (bilingual names, roles)
│   │   ├── project.py           # Project (intake_data JSONB)
│   │   ├── report.py            # ReportRun, ReportOutput, AgentLog
│   │   ├── subscription.py      # Moyasar subscription plans
│   │   ├── branding.py          # Branding assets
│   │   └── data_cache.py        # Seed data cache
│   ├── api/v1/                  # REST endpoints
│   │   ├── auth.py              # /auth/register, /auth/login
│   │   ├── projects.py          # Project CRUD
│   │   └── reports.py           # Report generation + SSE progress
│   ├── agents/                  # 15 specialized AI agents
│   │   ├── base_agent.py        # Abstract base with Claude tool_use loop
│   │   ├── intake_validation_agent.py
│   │   ├── sector_router_agent.py
│   │   ├── market_research_agent.py
│   │   ├── legal_regulatory_agent.py
│   │   ├── hr_saudization_agent.py
│   │   ├── franchise_agent.py
│   │   ├── real_estate_agent.py
│   │   ├── financial_modeling_agent.py
│   │   ├── competitive_analysis_agent.py
│   │   ├── vision2030_agent.py
│   │   ├── risk_assessment_agent.py
│   │   ├── chart_generation_agent.py   # Matplotlib, no Claude
│   │   ├── report_compiler_agent.py
│   │   ├── quality_review_agent.py
│   │   └── pdf_render_agent.py         # WeasyPrint, no Claude
│   ├── tasks/
│   │   ├── celery_app.py        # Celery config (Redis broker)
│   │   └── pipeline.py          # DAG orchestration (15 tiers)
│   └── pdf/
│       ├── templates/           # Jinja2 HTML (report_ar.html, report_en.html)
│       └── assets/              # CSS styling
├── alembic/                     # DB migrations (empty, needs initial migration)
├── Dockerfile
├── requirements.txt
└── .env.example
frontend/                        # Empty — Next.js app to be built
data-seed/                       # Saudi reference data JSONs
├── hrdf_nitaqat_ratios.json     # Saudization labor ratios
├── gastat_demographics.json     # Population/economic data
├── vision2030_kpis.json         # Vision 2030 KPIs
├── mci_licenses.json            # Ministry of Commerce licenses
├── rfta_franchises.json         # Saudi franchise data
└── sama_rates.json              # Central bank rates
docker-compose.yml
```

## Development Commands

```bash
# Start infrastructure
docker compose up postgres redis -d

# Backend (from /backend)
uvicorn app.main:app --reload --port 8000

# Celery worker (from /backend)
celery -A app.tasks.celery_app worker --concurrency=4

# Frontend (from /frontend, when implemented)
npm run dev  # port 3000
```

## Architecture

### Agent Pipeline (Celery DAG)

The core pipeline in `backend/app/tasks/pipeline.py` runs 15 agents across tiers:

1. **Tier 1** (sequential): IntakeValidation → SectorRouter
2. **Tier 2** (parallel, 4 agents): MarketResearch, LegalRegulatory, HRSaudization, [Franchise|RealEstate]
3. **Tier 2b** (parallel, 2 agents): FinancialModeling, CompetitiveAnalysis (depend on Tier 2)
4. **Tier 2c** (parallel, 2 agents): Vision2030, RiskAssessment (depend on all Tier 2)
5. **Tier 3** (sequential): ChartGeneration → ReportCompiler → QualityReview → PDFRender

### Base Agent Pattern

All agents inherit from `BaseAgent` (`backend/app/agents/base_agent.py`):
- Wraps Anthropic Claude API with tool_use loop
- Tracks tokens, timing, run_id
- Logs execution to `AgentLog` table
- Low temperature (0.3) for analytical accuracy
- Exceptions: ChartGenerationAgent (Matplotlib), PDFRenderAgent (WeasyPrint), SectorRouterAgent (pure Python)

### API Routes

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/auth/register` | POST | Create user |
| `/api/v1/auth/login` | POST | Get JWT token |
| `/api/v1/projects/` | POST/GET | Create/list projects |
| `/api/v1/projects/{id}/intake` | PUT | Update intake form |
| `/api/v1/reports/{project_id}/generate` | POST | Trigger pipeline |
| `/api/v1/reports/{run_id}/status` | GET | Check progress |
| `/api/v1/reports/{run_id}/stream` | GET | SSE real-time progress |
| `/api/v1/reports/{run_id}/download` | GET | Download PDF |

### Database Models

- UUID primary keys throughout
- JSONB columns for flexible data (`intake_data`, `pipeline_state`, `output_data`)
- Foreign keys with `back_populates` relationships
- Project statuses: `draft | processing | completed | failed`

### Bilingual Support

- Separate PDF templates: `report_ar.html` (RTL) and `report_en.html`
- User model has `full_name_ar`, `full_name_en`, `preferred_language`
- Project model has `name_ar`, `name_en`
- Arabic font rendering via Noto fonts (installed in Dockerfile)

## Code Conventions

### Python Style
- **snake_case** for functions/variables, **PascalCase** for classes
- Type hints throughout (from `typing` imports)
- Pydantic models for request/response validation
- SQLAlchemy models with declarative base

### Database
- **snake_case** for table and column names
- UUID primary keys (SQLAlchemy PostgreSQL UUID type)
- JSONB for semi-structured data
- Alembic for migrations (run from `/backend`)

### API
- RESTful routes under `/api/v1/`
- Snake_case JSON keys (Pydantic default)
- FastAPI dependency injection for auth (`get_current_user`)
- SSE for real-time progress streaming

## Environment Variables

See `backend/.env.example` for required variables:
- `DATABASE_URL` — PostgreSQL connection string
- `REDIS_URL` — Redis for Celery broker
- `ANTHROPIC_API_KEY` — Claude API key
- `CLAUDE_MODEL` — Model to use (default: claude-sonnet-4-6)
- `SECRET_KEY` — JWT signing key
- `AWS_*` / `S3_*` — Object storage credentials
- `MOYASAR_*` — Payment gateway keys
- `DATA_SEED_PATH` — Path to `/data-seed` directory

## Saudi Domain Context

- **Supported sectors** (15): retail, food_beverage, healthcare, education, technology, real_estate, manufacturing, logistics, hospitality, franchise, consulting, construction, agriculture, energy, finance
- **Regulatory bodies**: MCI, ZATCA, HRDF, SAMA, CMA, SFDA, MOH, CITC
- **Financial constants**: VAT 15%, Zakat 2.5%, SAIBOR 5.95%, SIDF rate 3.5%
- **Subscription plans**: Basic (SAR 99/mo, 2 reports), Pro (SAR 299/mo, 10 reports), Enterprise (SAR 799/mo, unlimited)

## Known Gaps

- No test suite (no pytest config or test files)
- No CI/CD pipeline (no GitHub Actions)
- No Alembic migrations generated yet
- Frontend not implemented
- Financial constants are hardcoded (marked for live SAMA feed integration)
- Some agents have broad exception handling that silently logs failures
