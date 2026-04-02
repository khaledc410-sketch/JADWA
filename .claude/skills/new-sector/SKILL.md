---
name: new-sector
description: Scaffold a new sector for JADWA — creates data seed, orchestrator, sub-agents, intake questions, and pipeline routing
disable-model-invocation: true
---

# New Sector Generator

Scaffolds all files needed to add a new business sector to JADWA.

## Usage

```
/new-sector <sector_name> <regulator> <sub_agent_1> <sub_agent_2> [sub_agent_3]
```

Example:
```
/new-sector agriculture mewa CropAnalysis LivestockRegulations
```

## What It Creates

### 1. Data Seed File
**Path**: `data-seed/<sector_name>.json`

JSON file with:
- `metadata` block (source, description_ar/en, last_updated)
- License types from the regulator
- Sector-specific regulations
- Salary benchmarks
- Compliance requirements

Follow the exact structure of `data-seed/mci_licenses.json`.

### 2. Data Tools Accessors
**Path**: `backend/app/services/data_tools.py`

Add to `filename_map` in `load_seed()`:
```python
"<sector_name>": "<sector_name>.json",
```

Add accessor functions:
```python
def get_<sector_name>_licenses() -> list:
    data = load_seed("<sector_name>")
    return data.get("licenses", [])
```

### 3. Orchestrator + Sub-Agents
**Path**: `backend/app/agents/<sector_name>/`

Files to create:
- `__init__.py` (empty)
- `orchestrator.py` — extends `SubAgentOrchestrator`
- `<sub_agent_1>_sub.py` — extends `BaseAgent`
- `<sub_agent_2>_sub.py` — extends `BaseAgent`

**CRITICAL patterns to follow**:
- Python 3.9 compatible (no `dict | list`, use `typing.Optional`)
- All `execute_tool` methods use `tool_input.get("field", default)` — NEVER `**kwargs`
- `max_tokens: int = 2000` for sub-agents
- `reviewer_max_tokens: int = 4000` for orchestrator
- Bilingual system prompts (Arabic first line, English instructions)
- Follow `backend/app/agents/franchise/orchestrator.py` as the reference pattern

### 4. Sector Router Update
**Path**: `backend/app/agents/sector_router_agent.py`

Add to `SECTOR_EXTRA_AGENTS`:
```python
"<sector_name>": ["<sector_name>"],
```

Add to `REPORT_TEMPLATES` if needed.
Add to `SECTOR_CONFIGS` with: nitaqat_min_percentage, vat_applicable, key_regulator.

### 5. Pipeline Update
**Path**: `backend/app/tasks/pipeline.py`

Add `elif sector == "<sector_name>":` block in Tier 2a parallel section.
Add `<sector_name>_result = {}` initialization.
Add to `all_results` dict.

### 6. Report Compiler Update
**Path**: `backend/app/agents/report_compiler_agent.py`

Add `"<sector_name>_analysis"` to `REPORT_SECTIONS` (as conditional).

### 7. Intake Wizard Questions
**Path**: `frontend/src/app/projects/new/page.tsx`

Add to `SECTOR_STEPS` with 3 steps of 4-5 professional questions each.
Add to `SECTORS` array with icon and Arabic description.

### 8. API Projects Update
**Path**: `backend/app/api/v1/projects.py`

Add to `VALID_SECTORS` set.

### 9. Report Progress Labels
**Path**: `frontend/src/app/reports/[runId]/page.tsx`

Add new agent names to `AGENT_LABELS` dict.

### 10. Landing Page
**Path**: `frontend/src/app/page.tsx`

Add sector card to the sectors grid.

## Verification Checklist

After creating all files:
- [ ] JSON seed file loads without errors (`load_seed("<sector_name>")`)
- [ ] Orchestrator imports and instantiates without errors
- [ ] Sub-agent tools call data_tools accessor functions correctly
- [ ] `SectorRouterAgent` routes to the new orchestrator
- [ ] Pipeline runs the new orchestrator in Tier 2a parallel
- [ ] Intake wizard shows new sector with questions
- [ ] Report progress page shows new agent labels
- [ ] Full E2E pipeline test passes for the new sector
