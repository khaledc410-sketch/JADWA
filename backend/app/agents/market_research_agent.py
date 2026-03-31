"""
MarketResearchAgent — generates Saudi market size analysis including
TAM/SAM/SOM, consumer segmentation, and 5-year growth projections.
Data is sourced from the Saudi data cache (mock for now).
"""

import json
from typing import Any

from app.agents.base_agent import BaseAgent


# ---------------------------------------------------------------------------
# Saudi market data cache (realistic mock — replace with live data later)
# ---------------------------------------------------------------------------

_SAUDI_MARKET_DATA = {
    "retail": {
        "tam_sar": 550_000_000_000,
        "sam_sar": 82_500_000_000,
        "growth_cagr_5yr": 0.07,
        "population": 36_000_000,
        "middle_class_pct": 0.62,
        "key_stat": "Saudi retail market reached SAR 550B in 2023 (GASTAT).",
    },
    "food_beverage": {
        "tam_sar": 110_000_000_000,
        "sam_sar": 16_500_000_000,
        "growth_cagr_5yr": 0.09,
        "population": 36_000_000,
        "middle_class_pct": 0.62,
        "key_stat": "F&B sector valued SAR 110B; CAGR 9% driven by Vision 2030 tourism.",
    },
    "healthcare": {
        "tam_sar": 145_000_000_000,
        "sam_sar": 43_500_000_000,
        "growth_cagr_5yr": 0.11,
        "population": 36_000_000,
        "middle_class_pct": 0.62,
        "key_stat": "Healthcare expenditure projected SAR 145B by 2025 (MOH).",
    },
    "education": {
        "tam_sar": 60_000_000_000,
        "sam_sar": 12_000_000_000,
        "growth_cagr_5yr": 0.08,
        "population": 36_000_000,
        "middle_class_pct": 0.62,
        "key_stat": "Private education market SAR 60B; 30% youth population under 15.",
    },
    "technology": {
        "tam_sar": 95_000_000_000,
        "sam_sar": 19_000_000_000,
        "growth_cagr_5yr": 0.18,
        "population": 36_000_000,
        "middle_class_pct": 0.62,
        "key_stat": "Saudi ICT market SAR 95B; Vision 2030 targets 50% digital economy.",
    },
    "real_estate": {
        "tam_sar": 700_000_000_000,
        "sam_sar": 210_000_000_000,
        "growth_cagr_5yr": 0.06,
        "population": 36_000_000,
        "middle_class_pct": 0.62,
        "key_stat": "Real estate contributes 6% of GDP; 70% home-ownership Vision 2030 target.",
    },
    "franchise": {
        "tam_sar": 55_000_000_000,
        "sam_sar": 11_000_000_000,
        "growth_cagr_5yr": 0.12,
        "population": 36_000_000,
        "middle_class_pct": 0.62,
        "key_stat": "Saudi franchise market SAR 55B; 10% annual growth (RFTA 2023).",
    },
    "manufacturing": {
        "tam_sar": 320_000_000_000,
        "sam_sar": 64_000_000_000,
        "growth_cagr_5yr": 0.10,
        "population": 36_000_000,
        "middle_class_pct": 0.62,
        "key_stat": "Manufacturing sector targeted at SAR 1T by 2030 (National Industrial Strategy).",
    },
    "logistics": {
        "tam_sar": 75_000_000_000,
        "sam_sar": 22_500_000_000,
        "growth_cagr_5yr": 0.13,
        "population": 36_000_000,
        "middle_class_pct": 0.62,
        "key_stat": "Logistics sector SAR 75B; Saudi targets top-10 logistics hub by 2030.",
    },
    "hospitality": {
        "tam_sar": 90_000_000_000,
        "sam_sar": 27_000_000_000,
        "growth_cagr_5yr": 0.16,
        "population": 36_000_000,
        "middle_class_pct": 0.62,
        "key_stat": "Tourism revenues SAR 90B; target 150M visitors by 2030.",
    },
    "default": {
        "tam_sar": 100_000_000_000,
        "sam_sar": 15_000_000_000,
        "growth_cagr_5yr": 0.08,
        "population": 36_000_000,
        "middle_class_pct": 0.62,
        "key_stat": "Saudi GDP SAR 4.2T (2023); robust SME growth environment.",
    },
}

_CONSUMER_SEGMENTS = [
    {
        "segment_en": "Young Professionals (25-40)",
        "segment_ar": "الشباب المهني (25-40 سنة)",
        "pct_population": 0.28,
        "avg_monthly_spend_sar": 6_500,
        "digital_savvy": True,
        "notes_en": "Largest growth segment; brand-conscious, mobile-first.",
        "notes_ar": "أكبر شريحة نمواً؛ واعية بالعلامات التجارية، تعتمد على الجوال.",
    },
    {
        "segment_en": "Families (30-55)",
        "segment_ar": "الأسر (30-55 سنة)",
        "pct_population": 0.35,
        "avg_monthly_spend_sar": 12_000,
        "digital_savvy": False,
        "notes_en": "Highest spending power; value quality and convenience.",
        "notes_ar": "أعلى قدرة إنفاق؛ تقدر الجودة والراحة.",
    },
    {
        "segment_en": "Saudi Gen-Z (18-25)",
        "segment_ar": "الجيل Z السعودي (18-25 سنة)",
        "pct_population": 0.22,
        "avg_monthly_spend_sar": 3_200,
        "digital_savvy": True,
        "notes_en": "Fastest-growing digital consumer; influenced by social media.",
        "notes_ar": "أسرع مستهلك رقمي نمواً؛ متأثر بوسائل التواصل الاجتماعي.",
    },
    {
        "segment_en": "Expat Residents",
        "segment_ar": "المقيمون الوافدون",
        "pct_population": 0.38,
        "avg_monthly_spend_sar": 5_000,
        "digital_savvy": True,
        "notes_en": "Large spending segment; brand-loyal, price-sensitive.",
        "notes_ar": "شريحة إنفاق كبيرة؛ مخلصة للعلامات التجارية وحساسة للأسعار.",
    },
]


class MarketResearchAgent(BaseAgent):
    name: str = "MarketResearchAgent"
    description: str = (
        "Saudi market size analysis, TAM/SAM/SOM, segmentation and growth"
    )

    @property
    def system_prompt(self) -> str:
        return (
            "أنت محلل أبحاث سوق أول متخصص في المملكة العربية السعودية، "
            "لديك معرفة عميقة ببيانات الهيئة العامة للإحصاء (GASTAT)، "
            "وأهداف رؤية 2030 القطاعية، وسلوك المستهلك السعودي.\n\n"
            "You are a senior market research analyst specializing in Saudi Arabia. "
            "You have deep knowledge of GASTAT data, Vision 2030 sector targets, "
            "and Saudi consumer behavior.\n\n"
            "Instructions:\n"
            "- Always write narrative sections in BOTH Arabic and English.\n"
            "- Use actual Saudi statistics (GASTAT, SAMA, sectoral reports).\n"
            "- TAM = total addressable Saudi market for the sector.\n"
            "- SAM = serviceable addressable market (realistic geographic/demographic slice).\n"
            "- SOM = serviceable obtainable market (realistic first 3-year capture).\n"
            "- All monetary values in SAR (ريال سعودي).\n"
            "- Return a single JSON object matching the output schema. "
            "  Do NOT include any text outside the JSON block."
        )

    @property
    def tools(self) -> list:
        return [
            {
                "name": "query_gastat_demographics",
                "description": (
                    "Queries the GASTAT demographic database for population statistics, "
                    "age distribution, urbanization rates, and income levels by region."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "region": {
                            "type": "string",
                            "description": "Saudi region or city",
                        },
                        "metric": {
                            "type": "string",
                            "description": "population | income | age_distribution | urbanization",
                        },
                    },
                    "required": ["metric"],
                },
            },
            {
                "name": "calculate_tam_sam_som",
                "description": (
                    "Calculates TAM, SAM, and SOM values for a given sector "
                    "using bottom-up and top-down methodologies."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sector": {"type": "string"},
                        "city": {"type": "string"},
                        "investment_sar": {"type": "number"},
                    },
                    "required": ["sector"],
                },
            },
            {
                "name": "fetch_sector_growth_data",
                "description": (
                    "Retrieves historical growth rates and 5-year CAGR projections "
                    "for a Saudi sector from Vision 2030 and industry reports."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sector": {"type": "string"},
                        "years": {
                            "type": "integer",
                            "description": "Projection years (default 5)",
                        },
                    },
                    "required": ["sector"],
                },
            },
            {
                "name": "generate_consumer_segments",
                "description": (
                    "Generates consumer segmentation data (demographics, spending, behavior) "
                    "for a Saudi sector and city."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sector": {"type": "string"},
                        "city": {"type": "string"},
                    },
                    "required": ["sector"],
                },
            },
        ]

    # ------------------------------------------------------------------
    # Tool implementations (Saudi data cache)
    # ------------------------------------------------------------------

    def execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        if tool_name == "query_gastat_demographics":
            return self._query_gastat_demographics(**tool_input)
        if tool_name == "calculate_tam_sam_som":
            return self._calculate_tam_sam_som(**tool_input)
        if tool_name == "fetch_sector_growth_data":
            return self._fetch_sector_growth_data(**tool_input)
        if tool_name == "generate_consumer_segments":
            return self._generate_consumer_segments(**tool_input)
        raise NotImplementedError(f"Unknown tool: {tool_name}")

    def _query_gastat_demographics(self, metric: str, region: str = "national") -> dict:
        return {
            "source": "GASTAT 2023",
            "region": region,
            "metric": metric,
            "data": {
                "total_population": 36_947_025,
                "saudi_nationals": 20_781_562,
                "expats": 16_165_463,
                "median_age": 29.4,
                "urbanization_rate": 0.845,
                "avg_household_income_sar": 14_800,
                "gdp_per_capita_sar": 112_500,
                "youth_under_30_pct": 0.52,
            },
        }

    def _calculate_tam_sam_som(
        self, sector: str, city: str = "riyadh", investment_sar: float = 1_000_000
    ) -> dict:
        data = _SAUDI_MARKET_DATA.get(sector.lower(), _SAUDI_MARKET_DATA["default"])
        tam = data["tam_sar"]
        sam = data["sam_sar"]
        # SOM: realistic 3-year penetration based on investment size
        penetration = min(investment_sar / sam * 15, 0.05)  # cap at 5%
        som = sam * penetration

        return {
            "sector": sector,
            "tam_sar": tam,
            "sam_sar": sam,
            "som_sar": round(som),
            "tam_usd": round(tam / 3.75),
            "sam_usd": round(sam / 3.75),
            "som_usd": round(som / 3.75),
            "methodology": "Top-down (GASTAT + sector reports) + Bottom-up (investment-scaled)",
            "key_stat": data["key_stat"],
        }

    def _fetch_sector_growth_data(self, sector: str, years: int = 5) -> dict:
        data = _SAUDI_MARKET_DATA.get(sector.lower(), _SAUDI_MARKET_DATA["default"])
        cagr = data["growth_cagr_5yr"]
        sam = data["sam_sar"]
        projections = []
        for yr in range(1, years + 1):
            projections.append(
                {
                    "year": 2024 + yr - 1,
                    "market_size_sar": round(sam * ((1 + cagr) ** yr)),
                }
            )
        return {
            "sector": sector,
            "cagr_5yr": cagr,
            "projections": projections,
            "drivers": [
                "Vision 2030 sector development targets",
                "Growing Saudi middle class",
                "Digital transformation initiative",
                "Rising tourist inflows",
                "Government SME support programs",
            ],
        }

    def _generate_consumer_segments(self, sector: str, city: str = "riyadh") -> dict:
        return {
            "sector": sector,
            "city": city,
            "segments": _CONSUMER_SEGMENTS,
            "total_addressable_consumers": 5_200_000,
        }

    def _build_user_message(self, context: dict) -> str:
        sector = context.get("sector", "default")
        city = context.get("city", "Riyadh")
        investment = context.get("investment_amount_sar", 1_000_000)
        language = context.get("language", "ar")

        return (
            f"Conduct a comprehensive Saudi market research analysis for this project.\n"
            f"Sector: {sector} | City: {city} | Investment: SAR {investment:,.0f}\n\n"
            f"Steps:\n"
            f"1. Call query_gastat_demographics for national population and income data.\n"
            f"2. Call calculate_tam_sam_som for {sector} in {city}.\n"
            f"3. Call fetch_sector_growth_data for {sector}.\n"
            f"4. Call generate_consumer_segments for {sector} in {city}.\n\n"
            f"Then synthesize all tool results into the output JSON schema:\n"
            f"market_size_sar, tam, sam, som, consumer_segments, growth_rate_5yr, "
            f"narrative_ar, narrative_en.\n\n"
            f"Preferred language: {language}\n\n"
            f"Full context:\n{json.dumps(context, ensure_ascii=False, indent=2)}"
        )
