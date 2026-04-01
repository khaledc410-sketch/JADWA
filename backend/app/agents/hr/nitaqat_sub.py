"""
NitaqatSubAgent -- Nitaqat (نطاقات) Saudization ratio calculations,
band classification, and compliance analysis.
"""

import math
from typing import Any

from app.agents.base_agent import BaseAgent
from app.services.data_tools import (
    get_nitaqat_thresholds,
    get_nitaqat_bands,
    normalize_sector,
)

# Fallback Nitaqat thresholds if seed data is unavailable
_FALLBACK_THRESHOLDS = {
    "platinum": 0.40,
    "high_green": 0.33,
    "low_green": 0.25,
    "yellow": 0.10,
}


class NitaqatSubAgent(BaseAgent):
    name: str = "NitaqatSubAgent"
    description: str = (
        "Nitaqat Saudization ratio calculations, band thresholds, "
        "and compliance analysis"
    )
    max_tokens: int = 2000
    temperature: float = 0.1

    @property
    def system_prompt(self) -> str:
        return (
            "أنت خبير في نظام نطاقات (السعودة) ومتطلبات الامتثال لنسب التوطين "
            "في المملكة العربية السعودية.\n\n"
            "You are a Saudi Nitaqat (نطاقات) Saudization compliance expert.\n\n"
            "Your responsibilities:\n"
            "- Calculate Saudization percentages for any sector and headcount.\n"
            "- Determine the Nitaqat band (platinum/high_green/low_green/yellow/red).\n"
            "- Provide sector-specific thresholds from MHRSD data.\n"
            "- Recommend how many additional Saudi hires are needed for compliance.\n"
            "- Provide bilingual band names (Arabic and English).\n"
            "- Return a JSON object with: nitaqat_percentage, nitaqat_band, "
            "nitaqat_band_ar, thresholds, compliant, recommendations.\n"
            "  No text outside the JSON block."
        )

    @property
    def tools(self) -> list:
        return [
            {
                "name": "calculate_nitaqat_ratio",
                "description": (
                    "Calculates the Nitaqat Saudization percentage and determines "
                    "the compliance band (platinum/high_green/low_green/yellow/red) "
                    "for a given sector and headcount."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sector": {"type": "string"},
                        "total_employees": {"type": "integer"},
                        "saudi_employees": {"type": "integer"},
                    },
                    "required": ["sector", "total_employees", "saudi_employees"],
                },
            },
        ]

    def execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        if tool_name == "calculate_nitaqat_ratio":
            return self._calculate_nitaqat_ratio(**tool_input)
        raise NotImplementedError(f"Unknown tool: {tool_name}")

    def _calculate_nitaqat_ratio(
        self, sector: str, total_employees: int, saudi_employees: int
    ) -> dict:
        pct = saudi_employees / total_employees if total_employees > 0 else 0

        # Try seed data first, fall back to hardcoded thresholds
        norm = normalize_sector(sector)
        thresholds = get_nitaqat_thresholds(norm)
        if not thresholds:
            thresholds = _FALLBACK_THRESHOLDS

        # Determine band
        if pct >= thresholds.get("platinum", 0.40):
            band = "platinum"
            band_ar = "البلاتيني"
        elif pct >= thresholds.get("high_green", 0.33):
            band = "high_green"
            band_ar = "الأخضر المرتفع"
        elif pct >= thresholds.get("low_green", 0.25):
            band = "low_green"
            band_ar = "الأخضر المنخفض"
        elif pct >= thresholds.get("yellow", 0.10):
            band = "yellow"
            band_ar = "الأصفر"
        else:
            band = "red"
            band_ar = "الأحمر"

        compliant = band not in ["yellow", "red"]

        recommendations = []
        if not compliant:
            needed = max(
                0,
                math.ceil(total_employees * thresholds.get("low_green", 0.25))
                - saudi_employees,
            )
            recommendations.append(
                f"Hire {needed} additional Saudi employee(s) to reach low_green band."
            )
        if band != "platinum":
            to_plat = max(
                0,
                math.ceil(total_employees * thresholds.get("platinum", 0.40))
                - saudi_employees,
            )
            recommendations.append(
                f"Hire {to_plat} additional Saudi employee(s) to reach platinum band."
            )

        return {
            "sector": norm,
            "nitaqat_percentage": round(pct * 100, 1),
            "nitaqat_band": band,
            "nitaqat_band_ar": band_ar,
            "saudi_count": saudi_employees,
            "total_headcount": total_employees,
            "expat_count": total_employees - saudi_employees,
            "thresholds": thresholds,
            "compliant": compliant,
            "to_reach_low_green": max(
                0,
                math.ceil(total_employees * thresholds.get("low_green", 0.25))
                - saudi_employees,
            ),
            "to_reach_platinum": max(
                0,
                math.ceil(total_employees * thresholds.get("platinum", 0.40))
                - saudi_employees,
            ),
            "recommendations": recommendations,
        }

    def _build_user_message(self, context: dict) -> str:
        sector = context.get("sector", "default")
        total = context.get("total_employees", context.get("total_headcount", 10))
        saudi = context.get("saudi_employees", context.get("saudi_count", 5))
        return (
            f"Calculate the Nitaqat Saudization compliance for this business.\n"
            f"Sector: {sector} | Total employees: {total} | Saudi employees: {saudi}\n\n"
            f"Call calculate_nitaqat_ratio with sector='{sector}', "
            f"total_employees={total}, saudi_employees={saudi}.\n\n"
            f"Return JSON with: nitaqat_percentage, nitaqat_band, nitaqat_band_ar, "
            f"thresholds, compliant, recommendations."
        )
