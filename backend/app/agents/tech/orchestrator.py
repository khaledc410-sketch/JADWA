"""
TechOrchestrator — runs CITC regulations and data compliance sub-agents
in parallel, then synthesizes a technology feasibility assessment for
Saudi Arabia.
"""

import json
from typing import Any

from app.agents.base_agent import BaseAgent, SubAgentOrchestrator
from app.agents.tech.citc_regulations_sub import CITCRegulationsSubAgent
from app.agents.tech.data_compliance_sub import DataComplianceSubAgent


class TechOrchestrator(SubAgentOrchestrator):
    name: str = "TechAgent"
    description: str = (
        "Orchestrates CITC licensing and data compliance sub-agents for "
        "technology sector feasibility"
    )
    temperature: float = 0.3

    def get_sub_agents(self, context: dict) -> list:
        return [
            CITCRegulationsSubAgent(db=self.db, run_id=self.run_id),
            DataComplianceSubAgent(db=self.db, run_id=self.run_id),
        ]

    @property
    def reviewer_system_prompt(self) -> str:
        return (
            "أنت مستشار تقنية أول متخصص في السوق السعودي.\n\n"
            "You are a senior technology consultant synthesizing CITC licensing "
            "and data compliance requirements into a comprehensive tech "
            "feasibility assessment for Saudi Arabia.\n\n"
            "Your role:\n"
            "- Cross-validate CITC license requirements with data compliance obligations.\n"
            "- Identify gaps between licensing status and data localization rules.\n"
            "- Assess overall technology venture viability: regulatory readiness, "
            "  data compliance posture, fintech sandbox eligibility, and risk factors.\n"
            "- Provide clear go/no-go recommendation with supporting evidence.\n"
            "- Include both Arabic and English narrative sections.\n\n"
            "Return a JSON object with:\n"
            "  citc_licenses, data_localization_requirements, pdpl_compliance,\n"
            "  fintech_sandbox_status (if applicable), ecommerce_requirements "
            "  (if applicable), total_licensing_cost_sar, compliance_flags,\n"
            "  viability_score (1-10), narrative_ar, narrative_en.\n"
            "No text outside the JSON block."
        )

    def _build_user_message(self, context: dict) -> str:
        business_name = context.get("business_name", "Tech Startup")
        business_activity = context.get(
            "business_activity", context.get("sector_detail", "technology services")
        )
        investment = context.get("investment_amount_sar", 1_000_000)
        city = context.get("city", "Riyadh")
        return (
            f"Conduct a full technology feasibility assessment for: {business_name}\n"
            f"Business activity: {business_activity}\n"
            f"Investment: SAR {investment:,.0f}\n"
            f"Target city: {city}\n\n"
            f"Steps:\n"
            f"1. Look up required CITC licenses for this technology activity.\n"
            f"2. Check fintech sandbox eligibility (if fintech-related).\n"
            f"3. Review data localization requirements for the data types involved.\n"
            f"4. Check PDPL compliance obligations.\n"
            f"5. Review e-commerce regulations (if applicable).\n\n"
            f"Return JSON with: citc_licenses, data_localization_requirements, "
            f"pdpl_compliance, fintech_sandbox_status, ecommerce_requirements, "
            f"total_licensing_cost_sar, compliance_flags, viability_score, "
            f"narrative_ar, narrative_en.\n\n"
            f"Full context:\n{json.dumps(context, ensure_ascii=False, indent=2)}"
        )
