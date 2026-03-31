"""
MarketOrchestrator — runs Demographics, MarketSizing, and ConsumerInsights
sub-agents in parallel, then synthesizes into a unified market research output.
"""

import json
from typing import Optional

from app.agents.base_agent import SubAgentOrchestrator
from app.agents.market.demographics_sub import DemographicsSubAgent
from app.agents.market.market_sizing_sub import MarketSizingSubAgent
from app.agents.market.consumer_insights_sub import ConsumerInsightsSubAgent


class MarketOrchestrator(SubAgentOrchestrator):
    name: str = "MarketResearchAgent"  # keep same name for pipeline compatibility
    description: str = (
        "Saudi market research orchestrator: demographics, market sizing, "
        "and consumer insights"
    )

    def get_sub_agents(self, context: dict) -> list:
        return [
            DemographicsSubAgent(db=self.db, run_id=self.run_id),
            MarketSizingSubAgent(db=self.db, run_id=self.run_id),
            ConsumerInsightsSubAgent(db=self.db, run_id=self.run_id),
        ]

    @property
    def reviewer_system_prompt(self) -> str:
        return (
            "أنت محلل أبحاث سوق أول متخصص في المملكة العربية السعودية. "
            "مهمتك هي مراجعة وتوحيد مخرجات ثلاثة وكلاء فرعيين: "
            "التركيبة السكانية، حجم السوق، ورؤى المستهلكين.\n\n"
            "You are a senior Saudi market analyst. Your task is to review "
            "and synthesize outputs from three sub-agents: Demographics, "
            "Market Sizing, and Consumer Insights.\n\n"
            "Instructions:\n"
            "- Cross-validate data across sub-agent outputs.\n"
            "- Resolve any conflicting numbers by choosing the most reliable source.\n"
            "- Produce bilingual narrative sections (Arabic and English).\n"
            "- All monetary values in SAR (ريال سعودي).\n"
            "- Final output must include: market_size_sar, tam, sam, som, "
            "consumer_segments, growth_rate_5yr, narrative_ar, narrative_en.\n"
            "- Return a single JSON object. No text outside the JSON block."
        )

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
