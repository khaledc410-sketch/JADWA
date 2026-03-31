"""
FranchiseEconomicsSubAgent — unit economics, territory analysis, and growth
modeling for franchise investments in the Saudi market.
"""

from typing import Any

from app.agents.base_agent import BaseAgent
from app.services.data_tools import lookup_franchise


class FranchiseEconomicsSubAgent(BaseAgent):
    name: str = "FranchiseEconomicsSubAgent"
    description: str = (
        "Franchise unit economics, territory analysis, and growth modeling"
    )
    max_tokens: int = 4096
    temperature: float = 0.2

    @property
    def system_prompt(self) -> str:
        return (
            "أنت متخصص في النمذجة المالية للامتياز التجاري في السوق السعودي.\n\n"
            "You are a franchise financial modeling specialist focused on the Saudi market.\n\n"
            "Your expertise:\n"
            "- Unit economics: revenue per unit, COGS, labor, rent, royalties, net margin.\n"
            "- ROI timeline: payback period, IRR, break-even analysis.\n"
            "- Territory analysis: city-level demand, competition density, demographic fit.\n"
            "- Multi-unit growth modeling: expansion timelines, capital requirements.\n"
            "- Saudi-specific factors: Saudization costs, VAT impact, GOSI contributions.\n\n"
            "Instructions:\n"
            "- Use realistic Saudi market benchmarks for costs and revenue.\n"
            "- Factor in franchise fees, ongoing royalties, and marketing contributions.\n"
            "- Model conservative, base, and optimistic scenarios.\n"
            "- All monetary values in SAR.\n"
            "- Return a JSON object with: unit_economics, roi_timeline, growth_projections.\n"
            "  No text outside the JSON block."
        )

    @property
    def tools(self) -> list:
        return [
            {
                "name": "analyze_unit_economics",
                "description": (
                    "Analyzes franchise unit economics given franchise data and investment amount. "
                    "Returns revenue breakdown, cost structure, ROI timeline, and break-even point."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "brand_name": {
                            "type": "string",
                            "description": "Franchise brand name for registry lookup",
                        },
                        "total_investment_sar": {
                            "type": "number",
                            "description": "Total investment amount in SAR",
                        },
                        "num_units": {
                            "type": "integer",
                            "description": "Number of franchise units (default: 1)",
                        },
                    },
                    "required": ["brand_name", "total_investment_sar"],
                },
            },
            {
                "name": "model_territory_growth",
                "description": (
                    "Models franchise territory growth projections for a given brand and city. "
                    "Returns demand estimates, competition analysis, and expansion timeline."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "brand_name": {
                            "type": "string",
                            "description": "Franchise brand name",
                        },
                        "city": {
                            "type": "string",
                            "description": "Target city in Saudi Arabia (e.g. Riyadh, Jeddah, Dammam)",
                        },
                    },
                    "required": ["brand_name", "city"],
                },
            },
        ]

    def execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        if tool_name == "analyze_unit_economics":
            return self._analyze_unit_economics(**tool_input)
        if tool_name == "model_territory_growth":
            return self._model_territory_growth(**tool_input)
        raise NotImplementedError(f"Unknown tool: {tool_name}")

    def _analyze_unit_economics(
        self,
        brand_name: str,
        total_investment_sar: float,
        num_units: int = 1,
    ) -> dict:
        franchise = lookup_franchise(brand_name)

        # Use registry data if available, otherwise apply generic benchmarks
        if franchise:
            avg_revenue = franchise.get("avg_unit_revenue_sar", 2_500_000)
            royalty_pct = franchise.get("royalty_percent", 6) / 100
            marketing_pct = franchise.get("marketing_fee_percent", 3) / 100
            franchise_fee = franchise.get("franchise_fee_sar", 150_000)
            break_even_months = franchise.get("break_even_months", 24)
        else:
            avg_revenue = 2_500_000
            royalty_pct = 0.06
            marketing_pct = 0.03
            franchise_fee = 150_000
            break_even_months = 24

        # Cost structure (Saudi market benchmarks)
        cogs_pct = 0.32
        labor_pct = 0.22
        rent_pct = 0.10
        other_opex_pct = 0.08

        gross_profit = avg_revenue * (1 - cogs_pct)
        total_opex = avg_revenue * (labor_pct + rent_pct + other_opex_pct)
        royalty_cost = avg_revenue * royalty_pct
        marketing_cost = avg_revenue * marketing_pct
        net_operating_income = gross_profit - total_opex - royalty_cost - marketing_cost

        per_unit_investment = total_investment_sar / num_units
        annual_roi_pct = (
            round((net_operating_income / per_unit_investment) * 100, 1)
            if per_unit_investment > 0
            else 0
        )
        payback_months = (
            round((per_unit_investment / net_operating_income) * 12)
            if net_operating_income > 0
            else None
        )

        return {
            "brand_name": brand_name,
            "num_units": num_units,
            "per_unit_investment_sar": round(per_unit_investment),
            "franchise_fee_sar": franchise_fee,
            "avg_annual_revenue_sar": round(avg_revenue),
            "cost_structure": {
                "cogs_pct": cogs_pct,
                "labor_pct": labor_pct,
                "rent_pct": rent_pct,
                "royalty_pct": royalty_pct,
                "marketing_pct": marketing_pct,
                "other_opex_pct": other_opex_pct,
            },
            "gross_profit_sar": round(gross_profit),
            "total_opex_sar": round(total_opex),
            "annual_royalty_sar": round(royalty_cost),
            "net_operating_income_sar": round(net_operating_income),
            "annual_roi_percent": annual_roi_pct,
            "payback_period_months": payback_months,
            "break_even_months": break_even_months,
            "scenarios": {
                "conservative": {
                    "revenue_multiplier": 0.75,
                    "net_income_sar": round(net_operating_income * 0.75),
                },
                "base": {
                    "revenue_multiplier": 1.0,
                    "net_income_sar": round(net_operating_income),
                },
                "optimistic": {
                    "revenue_multiplier": 1.25,
                    "net_income_sar": round(net_operating_income * 1.25),
                },
            },
        }

    def _model_territory_growth(self, brand_name: str, city: str) -> dict:
        # City population benchmarks (approximate)
        city_data = {
            "riyadh": {"population": 7_700_000, "growth_rate": 0.035, "tier": 1},
            "jeddah": {"population": 4_700_000, "growth_rate": 0.028, "tier": 1},
            "dammam": {"population": 1_300_000, "growth_rate": 0.032, "tier": 2},
            "mecca": {"population": 2_000_000, "growth_rate": 0.020, "tier": 1},
            "medina": {"population": 1_500_000, "growth_rate": 0.022, "tier": 2},
            "khobar": {"population": 600_000, "growth_rate": 0.030, "tier": 2},
        }

        city_key = city.lower().strip()
        cdata = city_data.get(
            city_key,
            {
                "population": 500_000,
                "growth_rate": 0.025,
                "tier": 3,
            },
        )

        franchise = lookup_franchise(brand_name)
        existing_units = franchise.get("total_units_saudi", 50) if franchise else 50

        # Estimate territory capacity based on population
        units_per_100k = 2.5 if cdata["tier"] == 1 else 1.8
        max_units = round(cdata["population"] / 100_000 * units_per_100k)
        estimated_existing = round(existing_units * (cdata["population"] / 35_000_000))
        available_slots = max(0, max_units - estimated_existing)

        return {
            "brand_name": brand_name,
            "city": city,
            "city_population": cdata["population"],
            "population_growth_rate": cdata["growth_rate"],
            "city_tier": cdata["tier"],
            "territory_analysis": {
                "max_units_capacity": max_units,
                "estimated_existing_units": estimated_existing,
                "available_slots": available_slots,
                "saturation_pct": round((estimated_existing / max_units) * 100, 1)
                if max_units > 0
                else 100,
            },
            "growth_projections": {
                "year_1": {
                    "new_units": min(1, available_slots),
                    "cumulative": estimated_existing + min(1, available_slots),
                },
                "year_3": {
                    "new_units": min(3, available_slots),
                    "cumulative": estimated_existing + min(3, available_slots),
                },
                "year_5": {
                    "new_units": min(5, available_slots),
                    "cumulative": estimated_existing + min(5, available_slots),
                },
            },
            "demand_drivers": [
                f"Population growth: {cdata['growth_rate'] * 100:.1f}% annually",
                f"City tier {cdata['tier']} — {'high' if cdata['tier'] == 1 else 'moderate'} commercial density",
                "Vision 2030 entertainment and lifestyle sector expansion",
                "Growing middle-class consumer spending",
            ],
        }
