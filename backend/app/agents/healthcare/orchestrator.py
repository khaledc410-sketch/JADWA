"""
HealthcareOrchestrator — runs MOH licensing, CCHI insurance, and medical
equipment sub-agents in parallel, then synthesizes a comprehensive healthcare
feasibility assessment.
"""

import json
from typing import Any

from app.agents.base_agent import BaseAgent, SubAgentOrchestrator
from app.agents.healthcare.moh_licensing_sub import MOHLicensingSubAgent
from app.agents.healthcare.cchi_insurance_sub import CCHIInsuranceSubAgent
from app.agents.healthcare.medical_equipment_sub import MedicalEquipmentSubAgent


class HealthcareOrchestrator(SubAgentOrchestrator):
    name: str = "HealthcareAgent"
    description: str = (
        "Orchestrates MOH licensing, CCHI insurance, and medical equipment sub-agents"
    )
    temperature: float = 0.3

    def get_sub_agents(self, context: dict) -> list:
        return [
            MOHLicensingSubAgent(db=self.db, run_id=self.run_id),
            CCHIInsuranceSubAgent(db=self.db, run_id=self.run_id),
            MedicalEquipmentSubAgent(db=self.db, run_id=self.run_id),
        ]

    @property
    def reviewer_system_prompt(self) -> str:
        return (
            "أنت مستشار رعاية صحية أول متخصص في السوق السعودي.\n\n"
            "You are a senior healthcare consultant synthesizing MOH licensing, "
            "CCHI insurance analysis, and medical equipment requirements into a "
            "comprehensive healthcare feasibility assessment.\n\n"
            "Your role:\n"
            "- Cross-validate MOH licensing requirements with CCHI insurance obligations.\n"
            "- Reconcile medical equipment costs with facility licensing tiers.\n"
            "- Assess CBAHI accreditation readiness and compliance gaps.\n"
            "- Evaluate staffing ratios against MOH minimums.\n"
            "- Provide clear viability score with supporting evidence.\n"
            "- Include both Arabic and English narrative sections.\n\n"
            "Return a JSON object with:\n"
            "  moh_licenses, total_licensing_cost_sar, cchi_category,\n"
            "  insurance_costs, equipment_costs, staffing_ratios,\n"
            "  cbahi_requirements, compliance_flags, viability_score (1-10),\n"
            "  narrative_ar, narrative_en.\n"
            "No text outside the JSON block."
        )

    def _build_user_message(self, context: dict) -> str:
        facility_type = context.get(
            "facility_type", context.get("business_type", "clinic")
        )
        city = context.get("city", "Riyadh")
        investment = context.get("investment_amount_sar", 2_000_000)
        employee_count = context.get("employee_count", 20)
        return (
            f"Conduct a full healthcare feasibility assessment for: {facility_type}\n"
            f"Investment: SAR {investment:,.0f}\n"
            f"Target city: {city}\n"
            f"Estimated employees: {employee_count}\n\n"
            f"Steps:\n"
            f"1. Look up MOH licensing requirements for this facility type.\n"
            f"2. Check CBAHI accreditation requirements.\n"
            f"3. Determine CCHI insurance category and calculate costs.\n"
            f"4. Estimate medical equipment and SFDA compliance costs.\n\n"
            f"Return JSON with: moh_licenses, total_licensing_cost_sar, cchi_category, "
            f"insurance_costs, equipment_costs, staffing_ratios, cbahi_requirements, "
            f"compliance_flags, viability_score, narrative_ar, narrative_en.\n\n"
            f"Full context:\n{json.dumps(context, ensure_ascii=False, indent=2)}"
        )
