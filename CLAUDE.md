# JADWA

Arabic-first AI feasibility study SaaS platform for Saudi Arabia. Generates 40-50 page branded PDF reports (Arabic + English) using a multi-agent Claude pipeline with sub-agent orchestration.

## Stack

- **Frontend:** Next.js 16 App Router, Tailwind CSS v4, Cairo font, Arabic RTL — port 3000
- **Backend:** FastAPI, SQLAlchemy, Alembic, Celery + Redis — port 8000
- **AI:** Anthropic Claude API (claude-sonnet-4-6) via tool_use — 19+ sub-agents across 6 domains
- **Database:** PostgreSQL 16
- **PDF:** WeasyPrint + Jinja2 (RTL HTML templates), fallback fpdf2
- **Storage:** MinIO (dev) / S3 (prod) for PDF reports
- **Payments:** Moyasar (Mada, VISA, Apple Pay — not yet integrated)
- **Infra:** Docker Compose (postgres, redis, minio, backend, celery_worker, frontend)

## Project Structure

```
backend/
  app/
    main.py                  # FastAPI entry point
    core/                    # config, database, security, deps
    models/                  # user, project, report, subscription, branding, data_cache
    api/v1/                  # auth, projects, reports, admin endpoints
    agents/                  # Sub-agent orchestration per domain:
      base_agent.py          # BaseAgent + SubAgentOrchestrator
      financial/             # SAMARates, PnLModeling, LoanScenario, InvestmentAnalysis + Reviewer
      market/                # Demographics, MarketSizing, ConsumerInsights + Reviewer
      legal/                 # Licensing, ForeignOwnership, SMEPrograms + Reviewer
      hr/                    # Nitaqat, Staffing, HRDFSubsidy + Reviewer
      vision/                # PillarAlignment, IncentivePrograms, GigaProjects + Reviewer
      franchise/             # RFTALookup, FranchiseEconomics + Reviewer
      competitive_analysis_agent.py   # Standalone
      risk_assessment_agent.py        # Standalone
      chart_generation_agent.py       # Standalone (matplotlib)
      report_compiler_agent.py        # Standalone
      quality_review_agent.py         # Standalone
      pdf_render_agent.py             # Standalone (WeasyPrint/fpdf2)
    services/
      data_tools.py          # Saudi seed data access (SAMA, RFTA, GASTAT, HRDF, Vision2030, MCI)
      storage.py             # S3/MinIO PDF storage
    tasks/                   # celery_app.py, pipeline.py (DAG orchestrator)
    pdf/templates/           # report_ar.html, report_en.html, report.css
  alembic/                   # DB migrations
  requirements.txt
data-seed/                   # Saudi data JSONs (6 files, 3400+ lines)
frontend/
  src/
    app/
      page.tsx               # Landing page
      layout.tsx             # Root layout (Cairo font, RTL)
      auth/                  # login, register
      dashboard/             # Projects dashboard
      projects/new/          # 7-step intake wizard
      reports/[runId]/       # Real-time pipeline progress
      admin/                 # Admin panel (stats, users, reports, data cache)
    lib/api.ts               # API client
docker-compose.yml
```

## Dev Setup

```bash
# Start infrastructure (postgres + redis + minio)
docker compose up -d postgres redis minio minio_init

# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Celery worker (separate terminal)
cd backend && celery -A app.tasks.celery_app worker --loglevel=info

# Frontend
cd frontend
npm install && npm run dev
```

Requires `ANTHROPIC_API_KEY` in `backend/.env` for agents to work.

## Agent Pipeline (Sub-Agent Architecture)

Each domain uses multiple specialized sub-agents run in parallel, then a reviewer agent synthesizes:

```
Tier 1 (sequential): IntakeValidation → SectorRouter
Tier 2 (parallel orchestrated domains):
  Financial:  SAMARates + PnLModeling + LoanScenario + InvestmentAnalysis → FinancialReviewer
  Market:     Demographics + MarketSizing + ConsumerInsights → MarketReviewer
  Legal:      Licensing + ForeignOwnership + SMEPrograms → LegalReviewer
  HR:         Nitaqat + Staffing + HRDFSubsidy → HRReviewer
  Vision2030: PillarAlignment + IncentivePrograms + GigaProjects → VisionReviewer
  Franchise:  RFTALookup + FranchiseEconomics → FranchiseReviewer (if sector=franchise)
Tier 3 (synthesis): ChartGeneration → ReportCompiler → QualityReview → PDFRender → S3 Upload
```

All agents inherit from `BaseAgent` (tool_use loop) or `SubAgentOrchestrator` (parallel sub-agents + reviewer).

## Data Sources

Agents use real Saudi data from `/data-seed/` via `app.services.data_tools`:
- `sama_rates.json` — SAIBOR, repo rates, VAT, Zakat, SIDF programs
- `rfta_franchises.json` — 847 registered franchises with RFTA metadata
- `gastat_demographics.json` — Population, cities, consumer segments
- `hrdf_nitaqat_ratios.json` — Nitaqat bands, salary benchmarks, GOSI rates
- `vision2030_kpis.json` — Pillars, giga-projects, incentive programs
- `mci_licenses.json` — Licensing requirements by sector

Never hardcode Saudi data — always use `from app.services.data_tools import ...`

## Conventions

- Arabic RTL is the primary direction. Always set `dir="rtl"` and use Cairo font.
- API base: `http://localhost:8000/api/v1/`
- Auth: JWT tokens (login/register in `backend/app/api/v1/auth.py`)
- Sectors: franchise, real_estate, fnb, retail
- All monetary values in SAR
- Agent system prompts are bilingual (Arabic first line, English instructions)
- Frontend: "use client" on all pages, Tailwind with CSS variables (jade/gold theme)

## Subscription Tiers

| Tier       | SAR/mo | Reports | Sectors | Languages |
|------------|--------|---------|---------|-----------|
| Basic      | 99     | 2       | 2       | AR only   |
| Pro        | 299    | 10      | All 4   | AR + EN   |
| Enterprise | 799    | Unlimited | All 4 | AR + EN + white-label |

## gstack

gstack is installed for development workflow. Available skills:
/office-hours, /plan-ceo-review, /plan-eng-review, /autoplan, /review, /qa, /ship, /cso, /investigate, /browse, /design-review, /retro, /learn
