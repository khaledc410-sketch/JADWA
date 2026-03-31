"""
FranchiseOrchestrator — runs RFTA lookup and economics sub-agents in parallel,
then synthesizes a franchise viability assessment.
"""

import json
from typing import Any

from app.agents.base_agent import BaseAgent, SubAgentOrchestrator
from app.agents.franchise.rfta_lookup_sub import RFTALookupSubAgent
from app.agents.franchise.franchise_economics_sub import FranchiseEconomicsSubAgent


class FranchiseOrchestrator(SubAgentOrchestrator):
    name: str = "FranchiseAgent"
    description: str = "Orchestrates RFTA lookup and franchise economics sub-agents"
    temperature: float = 0.3

    def get_sub_agents(self, context: dict) -> list:
        return [
            RFTALookupSubAgent(db=self.db, run_id=self.run_id),
            FranchiseEconomicsSubAgent(db=self.db, run_id=self.run_id),
        ]

    @property
    def reviewer_system_prompt(self) -> str:
        return (
            "أنت مستشار امتياز تجاري أول متخصص في السوق السعودي.\n\n"
            "You are a senior franchise consultant synthesizing RFTA registry data and "
            "financial economics into a comprehensive franchise viability assessment.\n\n"
            "Your role:\n"
            "- Cross-validate RFTA registration data with unit economics analysis.\n"
            "- Identify discrepancies between registry terms and financial projections.\n"
            "- Assess overall franchise viability: regulatory compliance, financial returns, "
            "  territory opportunity, and risk factors.\n"
            "- Provide clear go/no-go recommendation with supporting evidence.\n"
            "- Include both Arabic and English narrative sections.\n\n"
            "Return a JSON object with:\n"
            "  rfta_status, franchise_fee_sar, royalty_percent, territory_rights,\n"
            "  training_weeks, franchisor_support, unit_economics, territory_analysis,\n"
            "  viability_score (1-10), recommendation, risk_factors,\n"
            "  narrative_ar, narrative_en.\n"
            "No text outside the JSON block."
        )

    def _build_user_message(self, context: dict) -> str:
        brand = context.get(
            "franchise_brand", context.get("business_name", "Generic Franchise")
        )
        investment = context.get("investment_amount_sar", 1_500_000)
        city = context.get("city", "Riyadh")
        return (
            f"Conduct a full franchise viability assessment for: {brand}\n"
            f"Investment: SAR {investment:,.0f}\n"
            f"Target city: {city}\n\n"
            f"Steps:\n"
            f"1. Look up the brand in the RFTA registry.\n"
            f"2. Search for comparable franchises in the same sector.\n"
            f"3. Analyze unit economics with the investment amount.\n"
            f"4. Model territory growth for the target city.\n\n"
            f"Return JSON with: rfta_status, franchise_fee_sar, royalty_percent, "
            f"territory_rights, training_weeks, franchisor_support, unit_economics, "
            f"territory_analysis, viability_score, recommendation, risk_factors, "
            f"narrative_ar, narrative_en.\n\n"
            f"Full context:\n{json.dumps(context, ensure_ascii=False, indent=2)}"
        )
