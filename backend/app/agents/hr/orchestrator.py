"""
HROrchestrator -- runs Nitaqat, Staffing, and HRDF sub-agents in parallel,
then synthesizes results via a reviewer into a unified HR & Saudization plan.
"""

import json
from typing import Optional

from app.agents.base_agent import SubAgentOrchestrator
from app.agents.hr.nitaqat_sub import NitaqatSubAgent
from app.agents.hr.staffing_sub import StaffingSubAgent
from app.agents.hr.hrdf_subsidy_sub import HRDFSubsidySubAgent


class HROrchestrator(SubAgentOrchestrator):
    name: str = "HRSaudizationAgent"
    description: str = (
        "Orchestrates Nitaqat compliance, staffing plan, HRDF subsidies, "
        "and GOSI calculations via specialized sub-agents"
    )
    temperature: float = 0.2

    def get_sub_agents(self, context: dict) -> list:
        return [
            NitaqatSubAgent(db=self.db, run_id=self.run_id),
            StaffingSubAgent(db=self.db, run_id=self.run_id),
            HRDFSubsidySubAgent(db=self.db, run_id=self.run_id),
        ]

    @property
    def reviewer_system_prompt(self) -> str:
        return (
            "أنت استراتيجي موارد بشرية سعودي متقدم، تعمل على تحسين خطط التوظيف "
            "لتحقيق الامتثال لنظام نطاقات وتقليل التكاليف.\n\n"
            "You are a senior Saudi HR strategist optimizing staffing plans "
            "for Nitaqat compliance and cost efficiency.\n\n"
            "You have received outputs from three specialized sub-agents:\n"
            "1. NitaqatSubAgent -- Saudization ratio and band analysis\n"
            "2. StaffingSubAgent -- staffing plan with salaries and GOSI\n"
            "3. HRDFSubsidySubAgent -- HRDF/Nafis/Tamheer subsidies\n\n"
            "Your task:\n"
            "- Cross-validate the staffing plan against Nitaqat thresholds.\n"
            "- Ensure the Saudi/expat ratio achieves at least low_green band.\n"
            "- Optimize total labor cost by applying HRDF subsidies.\n"
            "- Calculate net annual labor cost (payroll + GOSI - subsidies).\n"
            "- Provide bilingual narrative (Arabic and English).\n"
            "- Return a single JSON object with: staffing_plan, total_headcount, "
            "saudi_count, nitaqat_percentage, nitaqat_band, "
            "hrdf_subsidy_year1_sar, total_annual_labor_cost_sar, "
            "narrative_ar, narrative_en.\n"
            "  No text outside the JSON block."
        )

    def _build_user_message(self, context: dict) -> str:
        sector = context.get("sector", "default")
        investment = context.get("investment_amount_sar", 2_000_000)
        city = context.get("city", "Riyadh")
        return (
            f"Build a comprehensive HR and Saudization plan for this Saudi business.\n"
            f"Sector: {sector} | Investment: SAR {investment:,.0f} | City: {city}\n\n"
            f"Steps:\n"
            f"1. Call build_staffing_plan to get recommended roles and headcount.\n"
            f"2. Call calculate_nitaqat_ratio using total and Saudi headcount from the plan.\n"
            f"3. Call fetch_hrdf_subsidies for Year 1 subsidy estimates.\n"
            f"4. Call estimate_gosi_contributions for the full staffing plan.\n\n"
            f"Return JSON: staffing_plan, total_headcount, saudi_count, nitaqat_percentage, "
            f"nitaqat_band, hrdf_subsidy_year1_sar, total_annual_labor_cost_sar, "
            f"narrative_ar, narrative_en.\n\n"
            f"Full context:\n{json.dumps(context, ensure_ascii=False, indent=2)}"
        )
