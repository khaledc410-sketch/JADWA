"""
GigaProjectsSubAgent — evaluates alignment with Saudi mega/giga-projects
(NEOM, Red Sea, Diriyah Gate, etc.) and Special Economic Zone benefits.
"""

from typing import Any

from app.agents.base_agent import BaseAgent
from app.services.data_tools import get_giga_projects, get_sez_benefits


class GigaProjectsSubAgent(BaseAgent):
    name: str = "GigaProjectsSubAgent"
    description: str = "Aligns project with Saudi giga-projects and SEZ benefits"
    max_tokens: int = 2000
    temperature: float = 0.2

    @property
    def system_prompt(self) -> str:
        return (
            "أنت متخصص في المشاريع العملاقة والمناطق الاقتصادية الخاصة في المملكة العربية السعودية، "
            "بما في ذلك نيوم، ومشروع البحر الأحمر، وبوابة الدرعية، والقدية.\n\n"
            "You are a Saudi mega-project and economic zone specialist with deep knowledge of:\n"
            "- NEOM (The Line, Oxagon, Trojena, Sindalah)\n"
            "- The Red Sea Global (tourism mega-project)\n"
            "- Diriyah Gate Development Authority\n"
            "- Qiddiya Entertainment City\n"
            "- King Abdullah Economic City (KAEC)\n"
            "- Special Economic Zones (SEZs) and their sector-specific benefits\n"
            "- Cloud Computing Zone (CCZ) in Riyadh\n"
            "- Jazan Special Economic Zone\n\n"
            "Your responsibilities:\n"
            "- Identify giga-projects relevant to the business sector.\n"
            "- Assess SEZ benefits (tax exemptions, customs, infrastructure).\n"
            "- Provide bilingual (Arabic and English) descriptions.\n"
            "- Return a JSON object with: giga_projects, sez_benefits. "
            "No text outside the JSON block."
        )

    @property
    def tools(self) -> list:
        return [
            {
                "name": "fetch_giga_projects",
                "description": (
                    "Returns Saudi mega/giga-projects relevant to the given sector, "
                    "including NEOM, Red Sea, Diriyah Gate, Qiddiya, and others."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sector": {
                            "type": "string",
                            "description": "Business sector to filter relevant giga-projects",
                        },
                    },
                    "required": [],
                },
            },
            {
                "name": "fetch_sez_benefits",
                "description": (
                    "Returns benefits of applicable Special Economic Zones (SEZs) "
                    "for a given sector, including tax exemptions, customs benefits, "
                    "and infrastructure support."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sector": {
                            "type": "string",
                            "description": "Business sector to check SEZ applicability",
                        },
                        "city": {
                            "type": "string",
                            "description": "Preferred city/location (optional)",
                        },
                    },
                    "required": ["sector"],
                },
            },
        ]

    def execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        if tool_name == "fetch_giga_projects":
            return self._fetch_giga_projects(**tool_input)
        if tool_name == "fetch_sez_benefits":
            return self._fetch_sez_benefits(**tool_input)
        raise NotImplementedError(f"Unknown tool: {tool_name}")

    def _fetch_giga_projects(self, sector: str = None) -> list:
        projects = get_giga_projects()

        if sector and projects:
            sector_lower = sector.lower()
            relevant = [
                p
                for p in projects
                if isinstance(p, dict)
                and (
                    sector_lower in [s.lower() for s in p.get("sectors", [])]
                    or sector_lower in p.get("description", "").lower()
                    or sector_lower in p.get("name_en", "").lower()
                )
            ]
            if relevant:
                return relevant

        return (
            projects
            if projects
            else [{"note": "No giga-project data available for this sector."}]
        )

    def _fetch_sez_benefits(self, sector: str, city: str = None) -> list:
        zones = get_sez_benefits(sector)

        if zones:
            return zones

        return [
            {
                "note": "No SEZ specifically targets this sector — standard MISA incentives apply."
            }
        ]
