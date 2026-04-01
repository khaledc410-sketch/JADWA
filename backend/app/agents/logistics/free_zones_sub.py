"""
FreeZonesSubAgent — searches Saudi free zones and calculates customs duties
for logistics feasibility assessments.
"""

from typing import Any

from app.agents.base_agent import BaseAgent
from app.services.data_tools import get_free_zones, get_customs_categories


class FreeZonesSubAgent(BaseAgent):
    name: str = "FreeZonesSubAgent"
    description: str = "Saudi free zone and customs duty specialist"
    max_tokens: int = 2000
    temperature: float = 0.2

    @property
    def system_prompt(self) -> str:
        return (
            "أنت متخصص في المناطق الحرة والجمارك في المملكة العربية السعودية.\n\n"
            "You are a Saudi free zone and customs specialist covering KAEC, "
            "ILBZ (Integrated Logistics Bonded Zone), and Jazan Economic City.\n\n"
            "Your expertise:\n"
            "- Free zone locations, benefits, tax incentives, and eligibility.\n"
            "- KAEC (King Abdullah Economic City) special economic zone.\n"
            "- ILBZ integrated logistics bonded zone operations.\n"
            "- Jazan Economic City industrial and logistics incentives.\n"
            "- ZATCA customs duty categories and tariff schedules.\n"
            "- Re-export, transit, and bonded warehouse regulations.\n\n"
            "Instructions:\n"
            "- Match regions to the most suitable free zone.\n"
            "- Compare free zone benefits vs. operating outside free zones.\n"
            "- Calculate applicable customs duties by product category.\n"
            "- All monetary values in SAR.\n"
            "- Return a JSON object with: free_zone_options, customs_duties, "
            "cost_comparison.\n"
            "  No text outside the JSON block."
        )

    @property
    def tools(self) -> list:
        return [
            {
                "name": "search_free_zones",
                "description": (
                    "Searches Saudi free zones by region. Returns free zone details, "
                    "benefits, tax incentives, and eligibility requirements."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "region": {
                            "type": "string",
                            "description": "Target region (e.g. Jeddah, KAEC, Jazan, Riyadh, Dammam)",
                        },
                    },
                    "required": ["region"],
                },
            },
            {
                "name": "calculate_customs_duties",
                "description": (
                    "Calculates customs duty rates for a given product category. "
                    "Returns ZATCA tariff rates, exemptions, and applicable agreements."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "product_category": {
                            "type": "string",
                            "description": "Product category (e.g. electronics, food, chemicals, textiles, machinery)",
                        },
                    },
                    "required": ["product_category"],
                },
            },
        ]

    def execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        if tool_name == "search_free_zones":
            return self._search_free_zones(tool_input)
        if tool_name == "calculate_customs_duties":
            return self._calculate_customs_duties(tool_input)
        raise NotImplementedError(f"Unknown tool: {tool_name}")

    # ── Tool implementations ──────────────────────────────────────────────

    def _search_free_zones(self, tool_input: dict) -> dict:
        region = tool_input.get("region", "Jeddah")
        zones = get_free_zones()
        region_lower = region.lower().strip()

        matching = [
            z
            for z in zones
            if region_lower in z.get("region", "").lower()
            or region_lower in z.get("city", "").lower()
            or region_lower in z.get("name", "").lower()
        ]

        if not matching:
            matching = zones  # return all as alternatives

        return {
            "search_region": region,
            "matching_zones": matching,
            "total_found": len(matching),
            "note": (
                "Free zones offer tax exemptions, customs duty benefits, "
                "and streamlined regulations. Compare with non-free-zone "
                "operations for cost-benefit analysis."
            ),
        }

    def _calculate_customs_duties(self, tool_input: dict) -> dict:
        product_category = tool_input.get("product_category", "general_goods")
        categories = get_customs_categories()
        cat_lower = product_category.lower().strip()

        matching = [
            c
            for c in categories
            if cat_lower in c.get("category", "").lower()
            or cat_lower in c.get("name", "").lower()
            or cat_lower in c.get("product_type", "").lower()
        ]

        if not matching:
            return {
                "product_category": product_category,
                "status": "not_found",
                "message": (
                    f"No specific customs category found for '{product_category}'. "
                    "Standard 5% VAT and applicable tariff rates apply."
                ),
                "all_categories": [
                    c.get("category", c.get("name", "")) for c in categories[:10]
                ],
            }

        return {
            "product_category": product_category,
            "status": "found",
            "matching_categories": matching,
            "total_matches": len(matching),
            "note": (
                "All imports subject to 15% VAT. Customs duties vary by HS code. "
                "GCC-origin goods may qualify for preferential rates."
            ),
        }
