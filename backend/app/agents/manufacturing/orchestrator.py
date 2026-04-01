"""
ManufacturingOrchestrator — runs MODON allocation and industrial licensing
sub-agents in parallel, then synthesizes a manufacturing feasibility assessment.
"""

import json
from typing import Any

from app.agents.base_agent import BaseAgent, SubAgentOrchestrator
from app.agents.manufacturing.modon_allocation_sub import MODONAllocationSubAgent
from app.agents.manufacturing.industrial_licensing_sub import (
    IndustrialLicensingSubAgent,
)


class ManufacturingOrchestrator(SubAgentOrchestrator):
    name: str = "ManufacturingAgent"
    description: str = (
        "Orchestrates MODON allocation and industrial licensing sub-agents"
    )
    temperature: float = 0.3

    def get_sub_agents(self, context: dict) -> list:
        return [
            MODONAllocationSubAgent(db=self.db, run_id=self.run_id),
            IndustrialLicensingSubAgent(db=self.db, run_id=self.run_id),
        ]

    @property
    def reviewer_system_prompt(self) -> str:
        return (
            "أنت مستشار صناعي أول متخصص في قطاع التصنيع في المملكة العربية السعودية.\n\n"
            "You are a senior industrial consultant synthesizing MODON industrial city "
            "allocation and licensing requirements into a comprehensive manufacturing "
            "feasibility assessment for Saudi Arabia.\n\n"
            "Your role:\n"
            "- Cross-validate MODON city allocation with licensing and compliance data.\n"
            "- Assess plot availability, infrastructure readiness, and cost efficiency.\n"
            "- Evaluate industrial licensing requirements and environmental compliance.\n"
            "- Analyze SIDF financing eligibility and NIC incentives.\n"
            "- Provide clear go/no-go recommendation with supporting evidence.\n"
            "- Include both Arabic and English narrative sections.\n\n"
            "Return a JSON object with:\n"
            "  modon_city_recommendation, plot_details, industrial_license,\n"
            "  sidf_financing, nic_incentives, environmental_compliance,\n"
            "  total_setup_cost_sar, compliance_flags, viability_score (1-10),\n"
            "  narrative_ar, narrative_en.\n"
            "No text outside the JSON block."
        )

    def _build_user_message(self, context: dict) -> str:
        business = context.get("business_name", "Manufacturing Project")
        industry = context.get("industry_type", context.get("sector", "general"))
        investment = context.get("investment_amount_sar", 5_000_000)
        city = context.get("city", "Riyadh")
        plot_size = context.get("plot_size_sqm", 5000)
        return (
            f"Conduct a full manufacturing feasibility assessment for: {business}\n"
            f"Industry type: {industry}\n"
            f"Investment: SAR {investment:,.0f}\n"
            f"Target city: {city}\n"
            f"Required plot size: {plot_size:,} sqm\n\n"
            f"Steps:\n"
            f"1. Search MODON industrial cities for available plots.\n"
            f"2. Compare industrial cities for the best fit.\n"
            f"3. Look up industrial licensing requirements.\n"
            f"4. Check environmental compliance requirements.\n"
            f"5. Review SIDF financing programs.\n\n"
            f"Return JSON with: modon_city_recommendation, plot_details, "
            f"industrial_license, sidf_financing, nic_incentives, "
            f"environmental_compliance, total_setup_cost_sar, compliance_flags, "
            f"viability_score, narrative_ar, narrative_en.\n\n"
            f"Full context:\n{json.dumps(context, ensure_ascii=False, indent=2)}"
        )
