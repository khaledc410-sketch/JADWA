"""
CCHIInsuranceSubAgent — retrieves CCHI insurance categories and calculates
mandatory health insurance costs for healthcare facility employees.
"""

import json
from typing import Any

from app.agents.base_agent import BaseAgent
from app.services.data_tools import get_cchi_categories


class CCHIInsuranceSubAgent(BaseAgent):
    name: str = "CCHIInsuranceSubAgent"
    description: str = "CCHI insurance category and cost calculation specialist"
    max_tokens: int = 2000
    temperature: float = 0.1

    @property
    def system_prompt(self) -> str:
        return (
            "أنت متخصص في التأمين الصحي الإلزامي ومجلس الضمان الصحي التعاوني (CCHI).\n\n"
            "You are a CCHI (Council of Cooperative Health Insurance) specialist "
            "with expertise in mandatory health insurance for Saudi Arabia.\n\n"
            "Your responsibilities:\n"
            "- Identify the correct CCHI insurance category for the facility type.\n"
            "- Calculate insurance costs based on employee count and facility classification.\n"
            "- Detail employer obligations under the cooperative health insurance law.\n"
            "- All monetary values in SAR.\n"
            "- Return a JSON object with: cchi_category, insurance_costs, obligations.\n"
            "  No text outside the JSON block."
        )

    @property
    def tools(self) -> list:
        return [
            {
                "name": "get_cchi_categories",
                "description": (
                    "Returns all CCHI insurance categories with coverage tiers, "
                    "premium ranges, and employer obligations."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
            {
                "name": "calculate_insurance_costs",
                "description": (
                    "Calculates estimated annual insurance costs for a healthcare facility "
                    "based on employee count and facility type."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "employee_count": {
                            "type": "integer",
                            "description": "Total number of employees requiring insurance coverage",
                        },
                        "facility_type": {
                            "type": "string",
                            "description": "Type of healthcare facility (e.g. hospital, clinic, pharmacy)",
                        },
                    },
                    "required": ["employee_count", "facility_type"],
                },
            },
        ]

    def execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        if tool_name == "get_cchi_categories":
            return self._get_cchi_categories()
        if tool_name == "calculate_insurance_costs":
            employee_count = tool_input.get("employee_count", 20)
            facility_type = tool_input.get("facility_type", "clinic")
            return self._calculate_insurance_costs(employee_count, facility_type)
        raise NotImplementedError(f"Unknown tool: {tool_name}")

    def _get_cchi_categories(self) -> list:
        return get_cchi_categories()

    def _calculate_insurance_costs(
        self, employee_count: int, facility_type: str
    ) -> dict:
        categories = get_cchi_categories()

        # Premium benchmarks per employee per year (SAR)
        # Healthcare workers typically require enhanced coverage
        premium_map = {
            "hospital": 6_500,
            "clinic": 4_500,
            "pharmacy": 3_500,
            "lab": 4_000,
            "dental_clinic": 4_200,
        }
        facility_lower = facility_type.lower().strip()
        per_employee = premium_map.get(facility_lower, 4_500)

        annual_total = per_employee * employee_count
        # GOSI health insurance contribution (employer share ~2%)
        gosi_contribution = int(annual_total * 0.02)

        return {
            "facility_type": facility_type,
            "employee_count": employee_count,
            "premium_per_employee_sar": per_employee,
            "annual_insurance_cost_sar": annual_total,
            "gosi_health_contribution_sar": gosi_contribution,
            "total_health_costs_sar": annual_total + gosi_contribution,
            "cchi_categories_available": categories,
            "notes": [
                "Healthcare workers require enhanced (Class A/B) coverage",
                "Employer bears 100% of employee insurance premiums",
                "Dependents coverage adds approximately 60-80% to base costs",
            ],
        }
