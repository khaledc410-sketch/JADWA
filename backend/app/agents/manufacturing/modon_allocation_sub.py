"""
MODONAllocationSubAgent — searches MODON industrial cities for available plots
and compares cities for optimal manufacturing site selection.
"""

from typing import Any

from app.agents.base_agent import BaseAgent
from app.services.data_tools import get_modon_cities


class MODONAllocationSubAgent(BaseAgent):
    name: str = "MODONAllocationSubAgent"
    description: str = "MODON industrial city allocation and plot search specialist"
    max_tokens: int = 2000
    temperature: float = 0.2

    @property
    def system_prompt(self) -> str:
        return (
            "أنت متخصص في تخصيص الأراضي الصناعية في المدن الصناعية السعودية (مدن).\n\n"
            "You are a MODON (Saudi Authority for Industrial Cities) allocation specialist.\n\n"
            "Your expertise:\n"
            "- Industrial city plot allocation across all MODON cities.\n"
            "- Plot sizes, costs per sqm, lease terms, and infrastructure availability.\n"
            "- Proximity to ports, airports, and logistics corridors.\n"
            "- Utility readiness: power, water, gas, wastewater treatment.\n"
            "- Comparison of industrial cities by sector suitability.\n\n"
            "Instructions:\n"
            "- Use official MODON data for plot pricing and availability.\n"
            "- Factor in infrastructure readiness and logistics connectivity.\n"
            "- All monetary values in SAR.\n"
            "- Return a JSON object with: city_recommendation, available_plots, "
            "infrastructure_assessment.\n"
            "  No text outside the JSON block."
        )

    @property
    def tools(self) -> list:
        return [
            {
                "name": "search_modon_plots",
                "description": (
                    "Searches MODON industrial cities for available plots matching "
                    "the specified city and plot size requirements. Returns matching "
                    "cities with plot details, pricing, and infrastructure data."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "Target city or region (e.g. Riyadh, Jeddah, Dammam, Jubail)",
                        },
                        "plot_size_sqm": {
                            "type": "number",
                            "description": "Required plot size in square meters",
                        },
                    },
                    "required": ["city"],
                },
            },
            {
                "name": "compare_industrial_cities",
                "description": (
                    "Compares all MODON industrial cities side-by-side on key metrics: "
                    "plot cost, infrastructure, logistics access, and sector focus."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        ]

    def execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        if tool_name == "search_modon_plots":
            return self._search_modon_plots(tool_input)
        if tool_name == "compare_industrial_cities":
            return self._compare_industrial_cities()
        raise NotImplementedError(f"Unknown tool: {tool_name}")

    # ── Tool implementations ──────────────────────────────────────────────

    def _search_modon_plots(self, tool_input: dict) -> dict:
        city = tool_input.get("city", "Riyadh")
        plot_size_sqm = tool_input.get("plot_size_sqm", 5000)

        cities = get_modon_cities()
        city_lower = city.lower().strip()

        matching = [
            c
            for c in cities
            if city_lower in c.get("city", "").lower()
            or city_lower in c.get("name", "").lower()
            or city_lower in c.get("region", "").lower()
        ]

        if not matching:
            matching = cities[:5]  # return top 5 as alternatives

        results = []
        for c in matching:
            min_plot = c.get("min_plot_sqm", 1000)
            max_plot = c.get("max_plot_sqm", 100000)
            cost_per_sqm = c.get("cost_per_sqm_sar", 50)
            fits = min_plot <= plot_size_sqm <= max_plot

            results.append(
                {
                    "city_name": c.get("name", c.get("city", "Unknown")),
                    "region": c.get("region", ""),
                    "plot_size_range_sqm": {"min": min_plot, "max": max_plot},
                    "cost_per_sqm_sar": cost_per_sqm,
                    "estimated_total_cost_sar": round(cost_per_sqm * plot_size_sqm),
                    "size_fits_requirement": fits,
                    "infrastructure": c.get("infrastructure", {}),
                    "sectors": c.get("sectors", c.get("focus_sectors", [])),
                    "occupancy_rate": c.get("occupancy_rate", None),
                }
            )

        return {
            "search_city": city,
            "required_plot_sqm": plot_size_sqm,
            "matching_cities": results,
            "total_found": len(results),
        }

    def _compare_industrial_cities(self) -> dict:
        cities = get_modon_cities()

        comparison = []
        for c in cities:
            comparison.append(
                {
                    "city_name": c.get("name", c.get("city", "Unknown")),
                    "region": c.get("region", ""),
                    "cost_per_sqm_sar": c.get("cost_per_sqm_sar", 0),
                    "infrastructure_score": c.get("infrastructure_score", None),
                    "logistics_access": c.get(
                        "logistics_access", c.get("port_access", "")
                    ),
                    "focus_sectors": c.get("sectors", c.get("focus_sectors", [])),
                    "occupancy_rate": c.get("occupancy_rate", None),
                    "total_area_sqm": c.get("total_area_sqm", None),
                }
            )

        # Sort by cost ascending
        comparison.sort(key=lambda x: x.get("cost_per_sqm_sar", 0))

        return {
            "total_cities": len(comparison),
            "cities": comparison,
            "note": "Sorted by cost per sqm (ascending). Consider logistics access and sector fit for final decision.",
        }
