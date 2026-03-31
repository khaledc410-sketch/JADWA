"""
ConsumerInsightsSubAgent — consumer segments, spending patterns, and digital adoption.
Sources: GASTAT consumer and population data.
"""

from typing import Any

from app.agents.base_agent import BaseAgent
from app.services.data_tools import get_consumer_segments, get_population_data


# Fallback consumer segments (used when seed files lack data)
_FALLBACK_SEGMENTS = [
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


class ConsumerInsightsSubAgent(BaseAgent):
    name: str = "ConsumerInsightsSubAgent"
    description: str = (
        "Saudi consumer segments, spending patterns, and digital adoption analysis"
    )

    @property
    def system_prompt(self) -> str:
        return (
            "أنت محلل سلوك المستهلك السعودي، متخصص في تحليل شرائح المستهلكين "
            "وأنماط الإنفاق والتبني الرقمي في المملكة العربية السعودية.\n\n"
            "You are a Saudi consumer behavior analyst specializing in consumer "
            "segments, spending patterns, and digital adoption in Saudi Arabia.\n\n"
            "Instructions:\n"
            "- Provide bilingual analysis (Arabic and English).\n"
            "- Segment consumers by demographics, spending power, and behavior.\n"
            "- Include digital adoption rates and e-commerce penetration.\n"
            "- Relate consumer insights to the target sector.\n"
            "- All monetary values in SAR.\n"
            "- Return a single JSON object. No text outside the JSON block."
        )

    @property
    def tools(self) -> list:
        return [
            {
                "name": "generate_consumer_segments",
                "description": (
                    "Returns demographic-based consumer profiles for a Saudi "
                    "sector including segment sizes, spending patterns, "
                    "digital savviness, and behavioral notes."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sector": {
                            "type": "string",
                            "description": "Business sector",
                        },
                        "city": {
                            "type": "string",
                            "description": "City for localized data (default: riyadh)",
                        },
                    },
                    "required": ["sector"],
                },
            },
        ]

    def execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        if tool_name == "generate_consumer_segments":
            return self._generate_consumer_segments(**tool_input)
        raise NotImplementedError(f"Unknown tool: {tool_name}")

    def _generate_consumer_segments(self, sector: str, city: str = "riyadh") -> dict:
        # Try seed data first
        segments = get_consumer_segments()
        if not segments:
            segments = _FALLBACK_SEGMENTS

        # Get population data for total addressable consumers estimate
        pop_data = get_population_data()
        total_pop = 36_947_025
        if isinstance(pop_data, dict):
            total_pop = pop_data.get("total_population", total_pop)

        # Estimate addressable consumers (urban, economically active)
        addressable = int(total_pop * 0.845 * 0.55)  # urban * economically active

        return {
            "sector": sector,
            "city": city,
            "segments": segments,
            "total_addressable_consumers": addressable,
        }

    def _build_user_message(self, context: dict) -> str:
        sector = context.get("sector", "default")
        city = context.get("city", "Riyadh")

        return (
            f"Analyze consumer segments for this project.\n"
            f"Sector: {sector} | City: {city}\n\n"
            f"Steps:\n"
            f"1. Call generate_consumer_segments for sector='{sector}' "
            f"in city='{city}'.\n\n"
            f"Return JSON with: consumer_segments (with bilingual descriptions), "
            f"total_addressable_consumers, spending_patterns, digital_adoption_insights, "
            f"key_opportunities (bilingual)."
        )
