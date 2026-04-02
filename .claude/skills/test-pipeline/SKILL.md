---
name: test-pipeline
description: Run a full E2E pipeline test — creates a test project, triggers report generation, and validates all agents complete successfully
disable-model-invocation: true
---

# Test Pipeline

Run a full end-to-end test of the JADWA report generation pipeline.

## Prerequisites

Before running, ensure:
1. PostgreSQL is running (`docker compose up postgres redis -d`)
2. Backend is running (`uvicorn app.main:app --reload`)
3. Celery worker is running (`celery -A app.tasks.celery_app worker`)
4. `ANTHROPIC_API_KEY` is set in the environment

## Steps

1. **Create a test user** (or use existing):
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email":"test@jadwa.sa","password":"Test123!","full_name_ar":"مستخدم تجريبي"}'
   ```

2. **Login and get token**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/login \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=test@jadwa.sa&password=Test123!"
   ```

3. **Create a test project** (use the simplest sector — retail):
   ```bash
   curl -X POST http://localhost:8000/api/v1/projects/ \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "sector": "retail",
       "name_ar": "متجر تجريبي",
       "name_en": "Test Store",
       "intake_data": {
         "user_goal": "new_idea",
         "business_stage": "new_idea",
         "city": "الرياض",
         "business_channel": "ecommerce",
         "product_category": "fashion",
         "investment_sar": "200000"
       }
     }'
   ```

4. **Generate report**:
   ```bash
   curl -X POST "http://localhost:8000/api/v1/reports/$PROJECT_ID/generate?language=ar" \
     -H "Authorization: Bearer $TOKEN"
   ```

5. **Poll status** until completed:
   ```bash
   curl "http://localhost:8000/api/v1/reports/$RUN_ID/status" \
     -H "Authorization: Bearer $TOKEN"
   ```

6. **Validate**:
   - Status should be `"completed"`
   - Progress should be `100`
   - `verdict_data` should be populated (check via `/verdict` endpoint)
   - `sections_data` should be populated (check via `/sections` endpoint)
   - Agent logs should show all agents completed (check via `/agent-logs` endpoint)
   - PDF should be downloadable (check via `/download` endpoint)

## What to Check After

- [ ] All 15+ agents show `status: completed` in agent logs
- [ ] `verdict_data` has `verdict_color`, `feasibility_score`, `irr_percent`
- [ ] `sections_data` has `executive_summary`, `financial_model`, `market_research`
- [ ] No agents show `status: failed`
- [ ] Total tokens used is under 100K (cost target: $1-2)
- [ ] Total pipeline time is under 10 minutes

## Common Failures

- **Rate limit (429)**: Check `max_workers=2` in pipeline.py, verify API tier
- **Import error**: Check Python 3.9 compatibility (no `dict | list` syntax)
- **Tool parameter mismatch**: Check `.get("field", default)` pattern in all `execute_tool` methods
- **Empty .env override**: Check config.py fallback reads `os.environ` when `.env` value is empty
