"""
EducationOrchestrator — runs MOE licensing and facility requirements sub-agents
in parallel, then synthesizes a comprehensive education feasibility assessment.
"""

import json
from typing import Any

from app.agents.base_agent import BaseAgent, SubAgentOrchestrator
from app.agents.education.moe_licensing_sub import MOELicensingSubAgent
from app.agents.education.facility_requirements_sub import FacilityRequirementsSubAgent


class EducationOrchestrator(SubAgentOrchestrator):
    name: str = "EducationAgent"
    description: str = "Orchestrates MOE licensing and facility requirements sub-agents"
    temperature: float = 0.3

    def get_sub_agents(self, context: dict) -> list:
        return [
            MOELicensingSubAgent(db=self.db, run_id=self.run_id),
            FacilityRequirementsSubAgent(db=self.db, run_id=self.run_id),
        ]

    @property
    def reviewer_system_prompt(self) -> str:
        return (
            "أنت مستشار تعليمي أول متخصص في السوق السعودي.\n\n"
            "You are a senior education consultant synthesizing MOE licensing "
            "and facility requirements into a comprehensive education feasibility "
            "assessment.\n\n"
            "Your role:\n"
            "- Cross-validate MOE licensing requirements with facility standards.\n"
            "- Reconcile teacher-student ratios with facility capacity.\n"
            "- Assess curriculum compliance and accreditation readiness.\n"
            "- Evaluate total setup costs including licensing, facility, and staffing.\n"
            "- Provide clear viability score with supporting evidence.\n"
            "- Include both Arabic and English narrative sections.\n\n"
            "Return a JSON object with:\n"
            "  school_type, moe_license_details, curriculum_requirements,\n"
            "  teacher_ratios, facility_sqm_requirements, total_setup_cost_sar,\n"
            "  compliance_flags, viability_score (1-10),\n"
            "  narrative_ar, narrative_en.\n"
            "No text outside the JSON block."
        )

    def _build_user_message(self, context: dict) -> str:
        school_type = context.get(
            "school_type", context.get("business_type", "international_school")
        )
        curriculum_type = context.get("curriculum_type", "international")
        city = context.get("city", "Riyadh")
        investment = context.get("investment_amount_sar", 3_000_000)
        student_capacity = context.get("student_capacity", 500)
        school_level = context.get("school_level", "k12")
        return (
            f"Conduct a full education feasibility assessment for: {school_type}\n"
            f"Curriculum: {curriculum_type}\n"
            f"Investment: SAR {investment:,.0f}\n"
            f"Target city: {city}\n"
            f"Student capacity: {student_capacity}\n"
            f"School level: {school_level}\n\n"
            f"Steps:\n"
            f"1. Look up MOE licensing requirements for this school type.\n"
            f"2. Check curriculum requirements and accreditation standards.\n"
            f"3. Calculate facility space requirements for the student capacity.\n"
            f"4. Determine teacher-student ratios and staffing needs.\n\n"
            f"Return JSON with: school_type, moe_license_details, curriculum_requirements, "
            f"teacher_ratios, facility_sqm_requirements, total_setup_cost_sar, "
            f"compliance_flags, viability_score, narrative_ar, narrative_en.\n\n"
            f"Full context:\n{json.dumps(context, ensure_ascii=False, indent=2)}"
        )
