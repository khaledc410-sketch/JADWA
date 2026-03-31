# JADWA (جدوى) — AI Feasibility Study Platform

> Arabic-first AI-powered feasibility study generator for the Saudi Arabian market

JADWA automates the creation of professional, data-driven feasibility studies. Entrepreneurs submit basic business information, and a pipeline of 15 specialized AI agents produces comprehensive bilingual (Arabic/English) PDF reports covering market analysis, financial projections, legal compliance, HR planning, and Vision 2030 alignment.

## Features

- **15-Agent AI Pipeline** — Specialized Claude-powered agents for market research, financial modeling, legal analysis, HR/Saudization planning, competitive analysis, risk assessment, and more
- **Arabic-First** — Native Arabic support with bilingual PDF output
- **Saudi-Specific** — Built-in knowledge of Saudi regulations (Nitaqat, SFDA, REGA, RFTA), tax codes (VAT 15%, Zakat 2.5%), and Vision 2030 KPIs
- **Real-Time Progress** — Server-Sent Events stream pipeline progress to the frontend
- **SaaS-Ready** — Three subscription tiers with Moyasar payment gateway integration
- **15+ Sectors** — Retail, F&B, Healthcare, Education, Technology, Real Estate, Franchise, Manufacturing, and more

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js, NextAuth.js, TypeScript |
| Backend | FastAPI, SQLAlchemy, Pydantic |
| AI | Anthropic Claude API (claude-sonnet-4-6) |
| Task Queue | Celery + Redis |
| Database | PostgreSQL 16 |
| PDF | WeasyPrint (Arabic text shaping) |
| Payments | Moyasar (Saudi gateway) |
| Storage | S3-compatible (AWS/MinIO/R2) |
| Infrastructure | Docker Compose |

## Quick Start

### 1. Start databases

```bash
docker compose up postgres redis -d
```

### 2. Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # Set ANTHROPIC_API_KEY
uvicorn app.main:app --reload --port 8000
```

### 3. Celery worker (separate terminal)

```bash
cd backend && source venv/bin/activate
celery -A app.tasks.celery_app worker --loglevel=info --concurrency=4
```

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:3000` (frontend) or `http://localhost:8000/docs` (API docs).

## Architecture

```
User → Next.js Frontend → FastAPI REST API → Celery Pipeline → Claude AI Agents
                                ↕                    ↕
                           PostgreSQL              Redis
```

### Agent Pipeline

Reports are generated through a tiered DAG pipeline:

1. **Validation** — IntakeValidation validates user input, SectorRouter determines agent activation
2. **Analysis** (parallel) — Market Research, Legal/Regulatory, HR/Saudization, plus sector-specific agents (Franchise or Real Estate)
3. **Modeling** (parallel) — Financial Modeling (5-year P&L, IRR, NPV), Competitive Analysis
4. **Assessment** (parallel) — Vision 2030 Alignment, Risk Assessment
5. **Synthesis** (sequential) — Chart Generation, Report Compilation, Quality Review, PDF Rendering

### Data Sources

Pre-loaded Saudi business data in `data-seed/`:
- GASTAT demographics and economic indicators
- SAMA monetary policy rates
- HRDF Nitaqat (Saudization) ratios by sector
- RFTA registered franchise database
- MCI business license requirements
- Vision 2030 KPIs and targets

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login |
| POST | `/api/v1/projects/` | Create project |
| GET | `/api/v1/projects/` | List projects |
| PUT | `/api/v1/projects/{id}/intake` | Update intake form |
| POST | `/api/v1/reports/{project_id}/generate` | Generate report |
| GET | `/api/v1/reports/{run_id}/status` | Check progress |
| GET | `/api/v1/reports/{run_id}/stream` | SSE progress stream |
| GET | `/api/v1/reports/{run_id}/download` | Download PDF |

## Subscription Tiers

| Plan | Price (SAR/mo) | Reports | Sectors | Languages | Pages |
|------|---------------|---------|---------|-----------|-------|
| Basic | 99 | 2 | 2 | Arabic | 40 |
| Pro | 299 | 10 | 4 | AR + EN | 50 |
| Enterprise | 799 | Unlimited | All | AR + EN | 55 |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Claude API key |
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `REDIS_URL` | Yes | Redis connection string |
| `SECRET_KEY` | Yes | JWT signing secret |
| `S3_BUCKET` | No | PDF storage bucket |
| `MOYASAR_SECRET_KEY` | No | Payment gateway key |

## License

Proprietary. All rights reserved.
