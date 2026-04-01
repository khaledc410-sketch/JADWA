"""
IndustrialLicensingSubAgent — looks up industrial licensing requirements,
environmental compliance, and SIDF financing programs for Saudi manufacturing.
"""

from typing import Any

from app.agents.base_agent import BaseAgent
from app.services.data_tools import (
    get_industrial_licenses,
    get_environmental_compliance,
    get_sidf_industrial_programs,
)


class IndustrialLicensingSubAgent(BaseAgent):
    name: str = "IndustrialLicensingSubAgent"
    description: str = "Saudi industrial licensing, environmental compliance, and SIDF financing specialist"
    max_tokens: int = 2000
    temperature: float = 0.2

    @property
    def system_prompt(self) -> str:
        return (
            "أنت متخصص في التراخيص الصناعية والامتثال البيئي في المملكة العربية السعودية.\n\n"
            "You are a Saudi industrial licensing and environmental compliance specialist.\n\n"
            "Your expertise:\n"
            "- Industrial license categories and requirements (MOCI, MODON).\n"
            "- NCEC (National Center for Environmental Compliance) regulations.\n"
            "- Environmental impact assessments and permits.\n"
            "- SIDF (Saudi Industrial Development Fund) financing programs.\n"
            "- NIC (National Industrial Center) incentives and support.\n\n"
            "Instructions:\n"
            "- Match industry types to correct license categories.\n"
            "- Identify all required environmental permits and compliance steps.\n"
            "- Recommend applicable SIDF financing programs.\n"
            "- All monetary values in SAR.\n"
            "- Return a JSON object with: license_requirements, environmental_permits, "
            "sidf_programs, estimated_costs.\n"
            "  No text outside the JSON block."
        )

    @property
    def tools(self) -> list:
        return [
            {
                "name": "lookup_industrial_license",
                "description": (
                    "Looks up industrial license requirements for a given industry type. "
                    "Returns license category, required documents, fees, and processing time."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "industry_type": {
                            "type": "string",
                            "description": "Type of industry (e.g. food_processing, chemicals, automotive, textiles)",
                        },
                    },
                    "required": ["industry_type"],
                },
            },
            {
                "name": "check_environmental_compliance",
                "description": (
                    "Checks environmental compliance requirements for a given industry type. "
                    "Returns NCEC permits, environmental impact assessment needs, and waste management rules."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "industry_type": {
                            "type": "string",
                            "description": "Type of industry to check compliance for",
                        },
                    },
                    "required": ["industry_type"],
                },
            },
            {
                "name": "get_sidf_programs_data",
                "description": (
                    "Retrieves all available SIDF (Saudi Industrial Development Fund) "
                    "financing programs for industrial projects. Returns loan types, "
                    "eligibility criteria, and terms."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        ]

    def execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        if tool_name == "lookup_industrial_license":
            return self._lookup_industrial_license(tool_input)
        if tool_name == "check_environmental_compliance":
            return self._check_environmental_compliance(tool_input)
        if tool_name == "get_sidf_programs_data":
            return self._get_sidf_programs_data()
        raise NotImplementedError(f"Unknown tool: {tool_name}")

    # ── Tool implementations ──────────────────────────────────────────────

    def _lookup_industrial_license(self, tool_input: dict) -> dict:
        industry_type = tool_input.get("industry_type", "general")
        licenses = get_industrial_licenses()
        industry_lower = industry_type.lower().strip()

        matching = [
            lic
            for lic in licenses
            if industry_lower in lic.get("industry_type", "").lower()
            or industry_lower in lic.get("category", "").lower()
            or industry_lower in lic.get("name", "").lower()
        ]

        if not matching:
            return {
                "industry_type": industry_type,
                "status": "not_found",
                "message": (
                    f"No specific license category found for '{industry_type}'. "
                    "A general industrial license (MOCI) may be required."
                ),
                "all_categories": [
                    lic.get("category", lic.get("name", "")) for lic in licenses[:10]
                ],
            }

        return {
            "industry_type": industry_type,
            "status": "found",
            "matching_licenses": matching,
            "total_matches": len(matching),
        }

    def _check_environmental_compliance(self, tool_input: dict) -> dict:
        industry_type = tool_input.get("industry_type", "general")
        compliance = get_environmental_compliance()

        return {
            "industry_type": industry_type,
            "compliance_data": compliance,
            "note": (
                "All industrial facilities require NCEC environmental clearance. "
                "High-impact industries (chemicals, petrochemicals, mining) require "
                "a full Environmental Impact Assessment (EIA)."
            ),
        }

    def _get_sidf_programs_data(self) -> dict:
        programs = get_sidf_industrial_programs()
        return {
            "total_programs": len(programs),
            "programs": programs,
            "note": (
                "SIDF provides up to 75% project financing for qualifying industrial "
                "projects. Repayment periods typically 10-20 years with grace periods."
            ),
        }
