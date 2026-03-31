"""
IncentiveProgramsSubAgent — matches a project to applicable Saudi government
incentive programs (grants, loans, subsidies, fee waivers).
"""

from typing import Any

from app.agents.base_agent import BaseAgent
from app.services.data_tools import get_incentive_programs


class IncentiveProgramsSubAgent(BaseAgent):
    name: str = "IncentiveProgramsSubAgent"
    description: str = (
        "Matches project to government incentive programs and support packages"
    )
    max_tokens: int = 4096
    temperature: float = 0.2

    @property
    def system_prompt(self) -> str:
        return (
            "أنت متخصص في برامج الحوافز والدعم الحكومي في المملكة العربية السعودية، "
            "بما في ذلك منشآت، وصندوق التنمية الصناعية، وهدف، ومسرعات الأعمال.\n\n"
            "You are a Saudi government incentive programs specialist with deep knowledge of:\n"
            "- Monsha'at SME support programs (financing, grants, mentorship)\n"
            "- SIDF (Saudi Industrial Development Fund) concessional loans\n"
            "- HRDF (Human Resources Development Fund) wage subsidies\n"
            "- MISA (Ministry of Investment) incentive packages\n"
            "- Sector-specific incentive programs (tourism, tech, manufacturing)\n"
            "- Nitaqat Saudization rewards and fee waivers\n\n"
            "Your responsibilities:\n"
            "- Identify all government incentive programs applicable to the given sector.\n"
            "- Include eligibility requirements, benefit amounts (SAR), and application URLs.\n"
            "- Provide bilingual (Arabic and English) program descriptions.\n"
            "- Return a JSON object with: sector, programs, total_programs, "
            "total_potential_benefit_sar. No text outside the JSON block."
        )

    @property
    def tools(self) -> list:
        return [
            {
                "name": "lookup_incentive_programs",
                "description": (
                    "Returns all government incentive programs applicable to a sector, "
                    "including grants, loans, subsidies, and fee waivers with eligibility "
                    "requirements and benefit amounts."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sector": {
                            "type": "string",
                            "description": "Business sector (e.g. technology, manufacturing, tourism)",
                        },
                        "investment_sar": {
                            "type": "number",
                            "description": "Planned investment amount in SAR",
                        },
                        "is_saudi_owned": {"type": "boolean"},
                    },
                    "required": ["sector"],
                },
            },
        ]

    def execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        if tool_name == "lookup_incentive_programs":
            return self._lookup_incentive_programs(**tool_input)
        raise NotImplementedError(f"Unknown tool: {tool_name}")

    def _lookup_incentive_programs(
        self,
        sector: str,
        investment_sar: float = 1_000_000,
        is_saudi_owned: bool = True,
    ) -> dict:
        programs = get_incentive_programs(sector)

        total_potential_benefit = sum(
            p.get("benefit_sar", 0) for p in programs if isinstance(p, dict)
        )

        return {
            "sector": sector,
            "programs": programs,
            "total_programs": len(programs),
            "total_potential_benefit_sar": total_potential_benefit,
            "note_ar": "المبالغ تقديرية وتخضع لشروط الأهلية",
            "note_en": "Amounts are indicative and subject to eligibility criteria",
        }
