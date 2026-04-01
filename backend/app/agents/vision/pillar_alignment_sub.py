"""
PillarAlignmentSubAgent — maps a project to Vision 2030 three pillars and their
strategic targets.
"""

from typing import Any

from app.agents.base_agent import BaseAgent
from app.services.data_tools import get_vision_pillars


class PillarAlignmentSubAgent(BaseAgent):
    name: str = "PillarAlignmentSubAgent"
    description: str = (
        "Maps project to Vision 2030 pillars and evaluates alignment scores"
    )
    max_tokens: int = 2000
    temperature: float = 0.2

    @property
    def system_prompt(self) -> str:
        return (
            "أنت متخصص في التوافق الاستراتيجي مع رؤية المملكة العربية السعودية 2030. "
            "لديك خبرة عميقة في الركائز الثلاث للرؤية وأهدافها ومؤشرات الأداء الرئيسية.\n\n"
            "You are a Vision 2030 strategic alignment specialist with deep expertise in:\n"
            "- The three Vision 2030 pillars: A Vibrant Society, A Thriving Economy, An Ambitious Nation\n"
            "- National Transformation Program (NTP) targets and KPIs\n"
            "- Sector-specific alignment with Vision 2030 programs\n"
            "- Saudi Content requirements and localization targets\n\n"
            "Your responsibilities:\n"
            "- Evaluate how a given business project aligns with Vision 2030 pillars.\n"
            "- Score alignment (0-100) based on sector, ownership, job creation, "
            "technology adoption, and export potential.\n"
            "- Identify relevant Vision 2030 targets and KPIs.\n"
            "- Provide bilingual (Arabic and English) narratives.\n"
            "- Return a JSON object with: alignment_score, aligned_pillars, pillar_details, "
            "alignment_factors. No text outside the JSON block."
        )

    @property
    def tools(self) -> list:
        return [
            {
                "name": "evaluate_vision_alignment",
                "description": (
                    "Evaluates the business project's alignment with Vision 2030 pillars "
                    "and National Transformation Program targets. Returns pillar alignment "
                    "scores and relevant targets."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sector": {
                            "type": "string",
                            "description": "Business sector (e.g. technology, manufacturing, tourism)",
                        },
                        "business_type": {
                            "type": "string",
                            "description": "Type of business (e.g. startup, SME, franchise, enterprise)",
                        },
                        "is_saudi_owned": {"type": "boolean"},
                        "creates_jobs": {"type": "boolean"},
                        "uses_technology": {"type": "boolean"},
                        "exports_potential": {"type": "boolean"},
                    },
                    "required": ["sector", "business_type"],
                },
            },
        ]

    def execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        if tool_name == "evaluate_vision_alignment":
            return self._evaluate_vision_alignment(**tool_input)
        raise NotImplementedError(f"Unknown tool: {tool_name}")

    def _evaluate_vision_alignment(
        self,
        sector: str,
        business_type: str = "SME",
        is_saudi_owned: bool = True,
        creates_jobs: bool = True,
        uses_technology: bool = False,
        exports_potential: bool = False,
    ) -> dict:
        pillars = get_vision_pillars()

        aligned_pillars = []
        for pillar_key, pillar in pillars.items():
            pillar_sectors = pillar.get("sectors", [])
            if "all" in pillar_sectors or sector.lower() in pillar_sectors:
                aligned_pillars.append(
                    {
                        "pillar_key": pillar_key,
                        "name_ar": pillar.get("name_ar", pillar_key),
                        "name_en": pillar.get("name_en", pillar_key),
                        "kpi": pillar.get("kpi", ""),
                    }
                )

        # Always include SME empowerment for SME business types
        if not any(p["pillar_key"] == "sme_empowerment" for p in aligned_pillars):
            sme = pillars.get("sme_empowerment", {})
            if sme:
                aligned_pillars.append(
                    {
                        "pillar_key": "sme_empowerment",
                        "name_ar": sme.get(
                            "name_ar", "تمكين المنشآت الصغيرة والمتوسطة"
                        ),
                        "name_en": sme.get("name_en", "SME Empowerment"),
                        "kpi": sme.get("kpi", ""),
                    }
                )

        # Compute base alignment score
        sector_base_scores = {
            "technology": 88,
            "manufacturing": 82,
            "logistics": 80,
            "real_estate": 75,
            "healthcare": 78,
            "education": 76,
            "food_beverage": 72,
            "franchise": 70,
            "retail": 68,
            "hospitality": 74,
            "energy": 85,
            "tourism": 80,
        }
        base = sector_base_scores.get(sector.lower(), 65)

        # Adjust for factors
        if is_saudi_owned:
            base = min(100, base + 3)
        if creates_jobs:
            base = min(100, base + 4)
        if uses_technology:
            base = min(100, base + 3)
        if exports_potential:
            base = min(100, base + 2)

        return {
            "sector": sector,
            "business_type": business_type,
            "alignment_score": round(base),
            "aligned_pillars": [p["pillar_key"] for p in aligned_pillars],
            "pillar_details": aligned_pillars,
            "alignment_factors": {
                "saudi_ownership": is_saudi_owned,
                "job_creation": creates_jobs,
                "technology_adoption": uses_technology,
                "export_potential": exports_potential,
            },
            "score_breakdown": {
                "economic_diversification": min(100, base + 5),
                "sme_empowerment": min(100, base + 3),
                "job_creation": min(100, base + 4),
                "technology_adoption": min(
                    100, base - 5 if sector.lower() != "technology" else base + 5
                ),
            },
            "benchmark": "Saudi national average SME alignment score: 72",
        }
