# CLAUDE.md — JADWA Project Guide

## Project Overview
JADWA (جدوى) is a Saudi-focused feasibility study generator powered by Claude AI agents.
The backend uses 15 specialized AI agents that call the Claude API to analyze business data
and generate comprehensive Arabic/English feasibility reports.

## Architecture
- **Backend**: Python / FastAPI (`backend/`)
- **Frontend**: Next.js (`frontend/`)
- **AI Agents**: All inherit from `backend/app/agents/base_agent.py`
- **Database**: PostgreSQL
- **Cache/Queue**: Redis + Celery
- **Payments**: Moyasar (Saudi gateway)

## Secrets & Configuration
- API keys and secrets live in `backend/.env` (gitignored, never committed)
- Copy `backend/.env.example` to `backend/.env` and fill in values
- The `ANTHROPIC_API_KEY` in `.env` is used by all 15 agents via `BaseAgent`
- Config is loaded by `backend/app/core/config.py` using pydantic-settings

### Required secrets in `backend/.env`:
| Variable | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | Claude API key for all AI agents |
| `CLAUDE_MODEL` | Model to use (default: `claude-sonnet-4-6`) |
| `SECRET_KEY` | JWT signing key for auth |
| `DATABASE_URL` | PostgreSQL connection string |
| `MOYASAR_SECRET_KEY` | Payment gateway (production) |

## AI Agent Pipeline
All agents read the `ANTHROPIC_API_KEY` from `backend/.env` via `settings.ANTHROPIC_API_KEY`.
The agent loop in `BaseAgent._run_agent_loop()` handles tool_use calls automatically.

To run an agent:
```python
from app.agents.sector_router_agent import SectorRouterAgent
agent = SectorRouterAgent(db=session, run_id="xxx")
result = agent.run(context={"project_name": "...", ...})
```

## Development Commands
```bash
# Backend
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend && npm install && npm run dev

# Docker (full stack)
docker-compose up
```

## Important Rules
- NEVER commit `backend/.env` — it contains real API keys
- Always use `.env.example` as the template for new environments
- The `.gitignore` already excludes `.env` and `.env.local`
