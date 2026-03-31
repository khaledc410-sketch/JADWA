"""
RealEstateAgent — real estate development analysis including REGA regulations,
property market data, construction costs, and development feasibility.
Activated only when sector == 'real_estate'.
"""

import json
from typing import Any

from app.agents.base_agent import BaseAgent


# ---------------------------------------------------------------------------
# Saudi real estate market data cache (mock — REGA/Ejar API later)
# ---------------------------------------------------------------------------

_CITY_RE_DATA = {
    "riyadh": {
        "avg_residential_sqm_sar": 4_500,
        "avg_commercial_sqm_sar": 7_200,
        "avg_land_sqm_sar": 2_800,
        "avg_construction_sqm_sar": 2_800,
        "avg_rental_yield_residential": 0.065,
        "avg_rental_yield_commercial": 0.082,
        "vacancy_rate": 0.12,
        "yoy_price_growth": 0.09,
        "demand_score": 8.5,
        "districts": ["النرجس", "حي الملقا", "العليا", "الرياض البلد", "حي الربوة"],
    },
    "jeddah": {
        "avg_residential_sqm_sar": 5_200,
        "avg_commercial_sqm_sar": 8_500,
        "avg_land_sqm_sar": 3_200,
        "avg_construction_sqm_sar": 2_900,
        "avg_rental_yield_residential": 0.060,
        "avg_rental_yield_commercial": 0.078,
        "vacancy_rate": 0.14,
        "yoy_price_growth": 0.07,
        "demand_score": 8.0,
        "districts": ["الشاطئ", "الحمراء", "السليمانية", "النزهة", "بحرة"],
    },
    "dammam": {
        "avg_residential_sqm_sar": 3_800,
        "avg_commercial_sqm_sar": 6_000,
        "avg_land_sqm_sar": 2_200,
        "avg_construction_sqm_sar": 2_600,
        "avg_rental_yield_residential": 0.070,
        "avg_rental_yield_commercial": 0.088,
        "vacancy_rate": 0.10,
        "yoy_price_growth": 0.08,
        "demand_score": 7.5,
        "districts": ["الفيصلية", "العنود", "الشاطئ الغربي", "الروضة", "المزروعية"],
    },
    "default": {
        "avg_residential_sqm_sar": 3_500,
        "avg_commercial_sqm_sar": 5_500,
        "avg_land_sqm_sar": 2_000,
        "avg_construction_sqm_sar": 2_500,
        "avg_rental_yield_residential": 0.068,
        "avg_rental_yield_commercial": 0.080,
        "vacancy_rate": 0.13,
        "yoy_price_growth": 0.06,
        "demand_score": 7.0,
        "districts": [],
    },
}


class RealEstateAgent(BaseAgent):
    name: str = "RealEstateAgent"
    description: str = "Saudi real estate development analysis with REGA compliance"
    temperature: float = 0.2

    @property
    def system_prompt(self) -> str:
        return (
            "أنت محلل عقاري سعودي متخصص في لوائح الهيئة العامة للعقارات (REGA)، "
            "وبيانات السوق العقاري حسب المدينة والحي، وتكاليف البناء، وجدوى التطوير.\n\n"
            "You are a Saudi real estate analyst with expertise in:\n"
            "- REGA (الهيئة العامة للعقارات) regulations and licensing\n"
            "- Saudi property market data by city and district\n"
            "- Construction costs and contractor benchmarks\n"
            "- Zoning, building permits, and municipality requirements\n"
            "- Rental yield analysis and capital appreciation\n"
            "- Vision 2030 housing and real estate targets\n\n"
            "Instructions:\n"
            "- Use current Saudi market prices per sqm.\n"
            "- Assess location quality with a score (0-100).\n"
            "- Calculate realistic development yields.\n"
            "- Include REGA compliance checklist.\n"
            "- Provide Arabic and English narratives.\n"
            "Return a JSON object matching the output schema exactly."
        )

    @property
    def tools(self) -> list:
        return [
            {
                "name": "analyze_location",
                "description": (
                    "Analyzes a Saudi real estate location for accessibility, "
                    "demographics, demand drivers, and development potential. "
                    "Returns a location score (0-100)."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string"},
                        "district": {"type": "string"},
                        "development_type": {
                            "type": "string",
                            "description": "residential | commercial | mixed_use | industrial",
                        },
                    },
                    "required": ["city"],
                },
            },
            {
                "name": "fetch_rega_market_data",
                "description": (
                    "Fetches current property prices per sqm, rental yields, "
                    "vacancy rates, and YoY growth from REGA data."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string"},
                        "property_type": {
                            "type": "string",
                            "description": "residential | commercial | land",
                        },
                    },
                    "required": ["city"],
                },
            },
            {
                "name": "estimate_construction_costs",
                "description": (
                    "Estimates total construction costs for a development project "
                    "including materials, labor, and contractor fees."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string"},
                        "total_area_sqm": {"type": "number"},
                        "development_type": {"type": "string"},
                        "spec_level": {
                            "type": "string",
                            "description": "economy | standard | premium | luxury",
                        },
                    },
                    "required": ["total_area_sqm", "development_type"],
                },
            },
            {
                "name": "check_zoning_compliance",
                "description": (
                    "Checks zoning regulations and building code compliance "
                    "for a development project in a Saudi city."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string"},
                        "district": {"type": "string"},
                        "development_type": {"type": "string"},
                        "floors": {"type": "integer"},
                        "land_area_sqm": {"type": "number"},
                    },
                    "required": ["city", "development_type"],
                },
            },
        ]

    # ------------------------------------------------------------------
    # Tool implementations
    # ------------------------------------------------------------------

    def execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        if tool_name == "analyze_location":
            return self._analyze_location(**tool_input)
        if tool_name == "fetch_rega_market_data":
            return self._fetch_rega_market_data(**tool_input)
        if tool_name == "estimate_construction_costs":
            return self._estimate_construction_costs(**tool_input)
        if tool_name == "check_zoning_compliance":
            return self._check_zoning_compliance(**tool_input)
        raise NotImplementedError(f"Unknown tool: {tool_name}")

    def _analyze_location(
        self, city: str, district: str = "", development_type: str = "residential"
    ) -> dict:
        city_data = _CITY_RE_DATA.get(city.lower(), _CITY_RE_DATA["default"])
        base_score = city_data["demand_score"] * 10  # 0-100

        type_adj = {
            "residential": 0,
            "commercial": 5,
            "mixed_use": 3,
            "industrial": -5,
        }
        score = min(100, base_score + type_adj.get(development_type, 0))

        return {
            "city": city,
            "district": district,
            "location_score": round(score),
            "demand_drivers": [
                f"Population growth rate: 2.3% annually",
                f"YoY price appreciation: {city_data['yoy_price_growth'] * 100:.0f}%",
                "Vision 2030 urban development projects nearby",
                "Growing expatriate workforce demand",
            ],
            "risks": [
                "Oversupply risk in certain sub-markets",
                f"Vacancy rate: {city_data['vacancy_rate'] * 100:.0f}%",
                "Interest rate sensitivity on financing",
            ],
            "recommended_development_type": development_type,
        }

    def _fetch_rega_market_data(
        self, city: str, property_type: str = "residential"
    ) -> dict:
        city_data = _CITY_RE_DATA.get(city.lower(), _CITY_RE_DATA["default"])
        if property_type == "commercial":
            price_sqm = city_data["avg_commercial_sqm_sar"]
            yield_pct = city_data["avg_rental_yield_commercial"]
        elif property_type == "land":
            price_sqm = city_data["avg_land_sqm_sar"]
            yield_pct = 0
        else:
            price_sqm = city_data["avg_residential_sqm_sar"]
            yield_pct = city_data["avg_rental_yield_residential"]

        return {
            "city": city,
            "property_type": property_type,
            "avg_price_sqm_sar": price_sqm,
            "avg_rental_yield_percent": round(yield_pct * 100, 1),
            "vacancy_rate_percent": round(city_data["vacancy_rate"] * 100, 1),
            "yoy_price_growth_percent": round(city_data["yoy_price_growth"] * 100, 1),
            "avg_construction_sqm_sar": city_data["avg_construction_sqm_sar"],
            "source": "REGA Market Report 2024",
            "comparable_districts": city_data["districts"][:3],
        }

    def _estimate_construction_costs(
        self,
        total_area_sqm: float,
        development_type: str,
        city: str = "riyadh",
        spec_level: str = "standard",
    ) -> dict:
        city_data = _CITY_RE_DATA.get(city.lower(), _CITY_RE_DATA["default"])
        base_cost_sqm = city_data["avg_construction_sqm_sar"]

        spec_multipliers = {
            "economy": 0.75,
            "standard": 1.0,
            "premium": 1.35,
            "luxury": 1.80,
        }
        type_multipliers = {
            "residential": 1.0,
            "commercial": 1.15,
            "mixed_use": 1.10,
            "industrial": 0.90,
        }

        adj_cost_sqm = (
            base_cost_sqm
            * spec_multipliers.get(spec_level, 1.0)
            * type_multipliers.get(development_type, 1.0)
        )
        total_construction = round(adj_cost_sqm * total_area_sqm)

        return {
            "total_area_sqm": total_area_sqm,
            "development_type": development_type,
            "spec_level": spec_level,
            "construction_cost_sqm_sar": round(adj_cost_sqm),
            "total_construction_cost_sar": total_construction,
            "soft_costs_15pct_sar": round(
                total_construction * 0.15
            ),  # Design, permits, consultancy
            "contingency_10pct_sar": round(total_construction * 0.10),
            "total_project_cost_sar": round(
                total_construction * 1.25
            ),  # Construction + soft + contingency
            "cost_breakdown": {
                "structure_sar": round(total_construction * 0.40),
                "mep_sar": round(total_construction * 0.25),
                "finishing_sar": round(total_construction * 0.25),
                "siteworks_sar": round(total_construction * 0.10),
            },
        }

    def _check_zoning_compliance(
        self,
        city: str,
        development_type: str,
        district: str = "",
        floors: int = 5,
        land_area_sqm: float = 1000,
    ) -> dict:
        max_floors_map = {
            "residential": 6,
            "commercial": 20,
            "mixed_use": 15,
            "industrial": 3,
        }
        max_floors = max_floors_map.get(development_type, 6)
        floor_area_ratio = 2.5  # Typical Saudi FAR

        return {
            "compliant": floors <= max_floors,
            "max_allowed_floors": max_floors,
            "requested_floors": floors,
            "floor_area_ratio": floor_area_ratio,
            "max_buildable_area_sqm": round(land_area_sqm * floor_area_ratio),
            "setback_requirements_m": {"front": 3, "side": 2, "rear": 2},
            "parking_spaces_required": max(
                1, round(land_area_sqm * floor_area_ratio / 50)
            ),
            "required_permits": [
                "Building Permit (رخصة البناء) — Balady",
                "Architectural Drawing Approval — Municipality",
                "Fire Safety Certificate — Civil Defense",
                "Structural Engineering Certificate — SBC",
                "Environmental Clearance (if applicable)",
            ],
            "compliance_notes": [
                f"Maximum height for {development_type} in {city}: {max_floors} floors",
                "Islamic architecture guidelines may apply in some districts",
                "REGA registration required before sales or leasing",
            ],
        }

    def _build_user_message(self, context: dict) -> str:
        city = context.get("city", "Riyadh")
        investment = context.get("investment_amount_sar", 5_000_000)
        dev_type = context.get("development_type", "residential")
        return (
            f"Conduct a full real estate development feasibility for this Saudi project.\n"
            f"City: {city} | Development Type: {dev_type} | Investment: SAR {investment:,.0f}\n\n"
            f"Steps:\n"
            f"1. Call analyze_location for {city}.\n"
            f"2. Call fetch_rega_market_data for {dev_type} in {city}.\n"
            f"3. Call estimate_construction_costs for the development.\n"
            f"4. Call check_zoning_compliance.\n\n"
            f"Return JSON: location_score, market_price_sqm_sar, rental_yield_percent, "
            f"construction_cost_sqm_sar, rega_compliance, comparable_projects, "
            f"narrative_ar, narrative_en.\n\n"
            f"Full context:\n{json.dumps(context, ensure_ascii=False, indent=2)}"
        )
