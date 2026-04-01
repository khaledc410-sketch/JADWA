"""
LogisticsOrchestrator — runs logistics licensing and free zones sub-agents
in parallel, then synthesizes a logistics feasibility assessment.
"""

import json
from typing import Any

from app.agents.base_agent import BaseAgent, SubAgentOrchestrator
from app.agents.logistics.logistics_licensing_sub import LogisticsLicensingSubAgent
from app.agents.logistics.free_zones_sub import FreeZonesSubAgent


class LogisticsOrchestrator(SubAgentOrchestrator):
    name: str = "LogisticsAgent"
    description: str = "Orchestrates logistics licensing and free zone sub-agents"
    temperature: float = 0.3

    def get_sub_agents(self, context: dict) -> list:
        return [
            LogisticsLicensingSubAgent(db=self.db, run_id=self.run_id),
            FreeZonesSubAgent(db=self.db, run_id=self.run_id),
        ]

    @property
    def reviewer_system_prompt(self) -> str:
        return (
            "أنت مستشار لوجستي أول متخصص في قطاع النقل والخدمات اللوجستية في المملكة العربية السعودية.\n\n"
            "You are a senior logistics consultant synthesizing transport licensing "
            "and free zone analysis into a comprehensive logistics feasibility "
            "assessment for Saudi Arabia.\n\n"
            "Your role:\n"
            "- Cross-validate transport licensing with free zone benefits and customs analysis.\n"
            "- Assess logistics hub suitability based on region, connectivity, and capacity.\n"
            "- Evaluate free zone incentives vs. operating outside free zones.\n"
            "- Analyze customs duty implications for the product categories.\n"
            "- Provide clear go/no-go recommendation with supporting evidence.\n"
            "- Include both Arabic and English narrative sections.\n\n"
            "Return a JSON object with:\n"
            "  transport_licenses, logistics_hub_recommendation,\n"
            "  free_zone_benefits, customs_analysis, total_licensing_cost_sar,\n"
            "  compliance_flags, viability_score (1-10),\n"
            "  narrative_ar, narrative_en.\n"
            "No text outside the JSON block."
        )

    def _build_user_message(self, context: dict) -> str:
        business = context.get("business_name", "Logistics Company")
        license_type = context.get(
            "license_type", context.get("logistics_type", "freight")
        )
        region = context.get("region", context.get("city", "Riyadh"))
        investment = context.get("investment_amount_sar", 2_000_000)
        product_category = context.get("product_category", "general_goods")
        return (
            f"Conduct a full logistics feasibility assessment for: {business}\n"
            f"License type: {license_type}\n"
            f"Target region: {region}\n"
            f"Investment: SAR {investment:,.0f}\n"
            f"Product category: {product_category}\n\n"
            f"Steps:\n"
            f"1. Look up transport licensing requirements.\n"
            f"2. Search for logistics hubs in the target region.\n"
            f"3. Search for applicable free zones.\n"
            f"4. Calculate customs duties for the product category.\n\n"
            f"Return JSON with: transport_licenses, logistics_hub_recommendation, "
            f"free_zone_benefits, customs_analysis, total_licensing_cost_sar, "
            f"compliance_flags, viability_score, narrative_ar, narrative_en.\n\n"
            f"Full context:\n{json.dumps(context, ensure_ascii=False, indent=2)}"
        )
