"""
TourismOrchestrator — runs STA licensing and entertainment permits sub-agents
in parallel, then synthesizes a tourism and hospitality feasibility assessment
for Saudi Arabia.
"""

import json
from typing import Any

from app.agents.base_agent import BaseAgent, SubAgentOrchestrator
from app.agents.tourism.sta_licensing_sub import STALicensingSubAgent
from app.agents.tourism.entertainment_permits_sub import EntertainmentPermitsSubAgent


class TourismOrchestrator(SubAgentOrchestrator):
    name: str = "TourismAgent"
    description: str = (
        "Orchestrates STA licensing and entertainment permits sub-agents for "
        "tourism sector feasibility"
    )
    temperature: float = 0.3

    def get_sub_agents(self, context: dict) -> list:
        return [
            STALicensingSubAgent(db=self.db, run_id=self.run_id),
            EntertainmentPermitsSubAgent(db=self.db, run_id=self.run_id),
        ]

    @property
    def reviewer_system_prompt(self) -> str:
        return (
            "أنت مستشار سياحة وضيافة أول متخصص في السوق السعودي.\n\n"
            "You are a senior tourism and hospitality consultant synthesizing "
            "STA licensing and entertainment permit requirements for Saudi Arabia.\n\n"
            "Your role:\n"
            "- Cross-validate STA license requirements with entertainment permit needs.\n"
            "- Assess hotel classification compliance where applicable.\n"
            "- Evaluate overall tourism venture viability: licensing readiness, "
            "  permit compliance, incentive eligibility, and risk factors.\n"
            "- Identify tourism incentives under Vision 2030 programs.\n"
            "- Provide clear go/no-go recommendation with supporting evidence.\n"
            "- Include both Arabic and English narrative sections.\n\n"
            "Return a JSON object with:\n"
            "  sta_licenses, hotel_classification (if applicable),\n"
            "  entertainment_permits, total_licensing_cost_sar,\n"
            "  tourism_incentives, compliance_flags,\n"
            "  viability_score (1-10), narrative_ar, narrative_en.\n"
            "No text outside the JSON block."
        )

    def _build_user_message(self, context: dict) -> str:
        business_name = context.get("business_name", "Tourism Venture")
        business_activity = context.get(
            "business_activity", context.get("sector_detail", "tourism and hospitality")
        )
        investment = context.get("investment_amount_sar", 2_000_000)
        city = context.get("city", "Riyadh")
        return (
            f"Conduct a full tourism and hospitality feasibility assessment for: "
            f"{business_name}\n"
            f"Business activity: {business_activity}\n"
            f"Investment: SAR {investment:,.0f}\n"
            f"Target city: {city}\n\n"
            f"Steps:\n"
            f"1. Look up required STA licenses for this tourism activity.\n"
            f"2. Check hotel classification requirements (if hotel-related).\n"
            f"3. Review GEA entertainment permit requirements (if applicable).\n"
            f"4. Identify tourism incentives and support programs.\n\n"
            f"Return JSON with: sta_licenses, hotel_classification, "
            f"entertainment_permits, total_licensing_cost_sar, tourism_incentives, "
            f"compliance_flags, viability_score, narrative_ar, narrative_en.\n\n"
            f"Full context:\n{json.dumps(context, ensure_ascii=False, indent=2)}"
        )
