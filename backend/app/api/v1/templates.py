from fastapi import APIRouter, HTTPException
from typing import Optional

from app.services.data_tools import get_templates, get_template

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("/")
def list_templates(sector: Optional[str] = None):
    """List all project templates, optionally filtered by sector."""
    templates = get_templates(sector=sector)
    return {
        "templates": [
            {
                "id": t.get("id"),
                "name_ar": t.get("name_ar"),
                "name_en": t.get("name_en"),
                "sector": t.get("sector"),
                "icon": t.get("icon"),
                "typical_investment_sar": t.get("typical_investment_sar"),
                "typical_irr": t.get("typical_irr"),
                "description_ar": t.get("description_ar"),
            }
            for t in templates
        ],
        "total": len(templates),
    }


@router.get("/{template_id}")
def get_template_detail(template_id: str):
    """Get a single template with its prefill data."""
    template = get_template(template_id)
    if not template:
        raise HTTPException(404, f"Template '{template_id}' not found")
    return template
