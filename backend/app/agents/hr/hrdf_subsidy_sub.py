"""
HRDFSubsidySubAgent -- HRDF training programs, Nafis, Tamheer subsidies
and Saudi workforce development incentives.
"""

from typing import Any

from app.agents.base_agent import BaseAgent
from app.services.data_tools import get_hrdf_subsidy_info

# Fallback HRDF constants
_HRDF_SUBSIDY_RATE = 0.50
_HRDF_MAX_MONTHLY_SAR = 4_000


class HRDFSubsidySubAgent(BaseAgent):
    name: str = "HRDFSubsidySubAgent"
    description: str = (
        "HRDF training programs, Nafis, Tamheer subsidies, "
        "and Saudi workforce development incentives"
    )
    max_tokens: int = 2000
    temperature: float = 0.1

    @property
    def system_prompt(self) -> str:
        return (
            "أنت متخصص في برامج صندوق تنمية الموارد البشرية (هدف) وبرنامج نافس "
            "وبرنامج تمهير لدعم التوظيف والتدريب في المملكة العربية السعودية.\n\n"
            "You are a Saudi HR development and training programs specialist "
            "with deep knowledge of:\n"
            "- HRDF (صندوق تنمية الموارد البشرية / Hadaf) subsidy programs\n"
            "- Nafis (نافس) private sector employment support\n"
            "- Tamheer (تمهير) on-the-job training program\n"
            "- Graduate hiring subsidies\n"
            "- Saudization premium incentives for Nitaqat platinum companies\n\n"
            "Your responsibilities:\n"
            "- List available HRDF/Nafis/Tamheer programs with eligibility criteria.\n"
            "- Calculate estimated subsidy amounts based on Saudi headcount.\n"
            "- Provide program durations and maximum benefit caps.\n"
            "- Provide bilingual program names (Arabic and English).\n"
            "- All monetary values in SAR.\n"
            "- Return a JSON object with: programs, total_annual_subsidy_sar, "
            "monthly_subsidy_per_hire_sar.\n"
            "  No text outside the JSON block."
        )

    @property
    def tools(self) -> list:
        return [
            {
                "name": "fetch_hrdf_subsidies",
                "description": (
                    "Returns available HRDF, Nafis, and Tamheer subsidy programs "
                    "for Saudi hires, including eligibility, subsidy amounts, "
                    "and program durations."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sector": {"type": "string"},
                        "saudi_headcount": {"type": "integer"},
                        "avg_salary_sar": {"type": "number"},
                    },
                    "required": ["saudi_headcount"],
                },
            },
        ]

    def execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        if tool_name == "fetch_hrdf_subsidies":
            return self._fetch_hrdf_subsidies(**tool_input)
        raise NotImplementedError(f"Unknown tool: {tool_name}")

    def _fetch_hrdf_subsidies(
        self,
        saudi_headcount: int,
        sector: str = "default",
        avg_salary_sar: float = 6_000,
    ) -> dict:
        # Try seed data first
        hrdf_data = get_hrdf_subsidy_info()
        subsidy_rate = hrdf_data.get("subsidy_rate", _HRDF_SUBSIDY_RATE)
        max_monthly = hrdf_data.get("max_monthly_sar", _HRDF_MAX_MONTHLY_SAR)

        monthly_subsidy_per_hire = min(avg_salary_sar * subsidy_rate, max_monthly)
        annual_subsidy = round(monthly_subsidy_per_hire * 12 * saudi_headcount)

        programs = [
            {
                "program_name_en": "HRDF On-the-Job Training Subsidy",
                "program_name_ar": "دعم التدريب على رأس العمل",
                "benefit": (
                    f"50% of salary up to SAR {max_monthly:,.0f}/month "
                    f"per hire for 12 months"
                ),
                "max_duration_months": 12,
                "eligible_headcount": saudi_headcount,
                "estimated_benefit_sar": annual_subsidy,
            },
            {
                "program_name_en": "Nafis Private Sector Support",
                "program_name_ar": "برنامج نافس لدعم القطاع الخاص",
                "benefit": (
                    "SAR 3,000/month salary supplement for Saudi employees "
                    "in private sector for up to 24 months"
                ),
                "max_duration_months": 24,
                "eligible_headcount": saudi_headcount,
                "estimated_benefit_sar": round(saudi_headcount * 3_000 * 12),
            },
            {
                "program_name_en": "Tamheer On-the-Job Training",
                "program_name_ar": "برنامج تمهير للتدريب على رأس العمل",
                "benefit": (
                    "SAR 3,000/month training allowance for Saudi graduates "
                    "for 3-6 months"
                ),
                "max_duration_months": 6,
                "eligible_headcount": round(saudi_headcount * 0.2),
                "estimated_benefit_sar": round(saudi_headcount * 0.2 * 3_000 * 6),
            },
            {
                "program_name_en": "Saudization Premium (Nitaqat Platinum)",
                "program_name_ar": "مكافأة السعودة - مستوى البلاتيني",
                "benefit": (
                    "Priority access to government procurement and reduced CR fees"
                ),
                "max_duration_months": 36,
                "eligible_headcount": saudi_headcount,
                "estimated_benefit_sar": 15_000,
            },
            {
                "program_name_en": "HRDF Graduate Hiring Program",
                "program_name_ar": "برنامج توظيف الخريجين",
                "benefit": (
                    "SAR 2,000/month subsidy for fresh Saudi graduates (first 2 years)"
                ),
                "max_duration_months": 24,
                "eligible_headcount": round(saudi_headcount * 0.3),
                "estimated_benefit_sar": round(saudi_headcount * 0.3 * 2_000 * 12),
            },
        ]

        return {
            "sector": sector,
            "saudi_headcount": saudi_headcount,
            "monthly_subsidy_per_hire_sar": round(monthly_subsidy_per_hire),
            "total_annual_subsidy_sar": annual_subsidy,
            "programs": programs,
        }

    def _build_user_message(self, context: dict) -> str:
        sector = context.get("sector", "default")
        saudi_count = context.get("saudi_count", context.get("saudi_employees", 5))
        avg_salary = context.get("avg_salary_sar", 6_000)
        return (
            f"List available HRDF and workforce development subsidies.\n"
            f"Sector: {sector} | Saudi headcount: {saudi_count} | "
            f"Avg salary: SAR {avg_salary:,.0f}\n\n"
            f"Call fetch_hrdf_subsidies with saudi_headcount={saudi_count}, "
            f"sector='{sector}', avg_salary_sar={avg_salary}.\n\n"
            f"Return JSON with: programs, total_annual_subsidy_sar, "
            f"monthly_subsidy_per_hire_sar."
        )
