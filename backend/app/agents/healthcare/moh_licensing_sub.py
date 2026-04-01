"""
MOHLicensingSubAgent — looks up MOH facility license types and CBAHI
accreditation requirements for healthcare feasibility studies.
"""

import json
from typing import Any

from app.agents.base_agent import BaseAgent
from app.services.data_tools import get_moh_licenses, get_cbahi_requirements


class MOHLicensingSubAgent(BaseAgent):
    name: str = "MOHLicensingSubAgent"
    description: str = "MOH licensing and CBAHI accreditation specialist"
    max_tokens: int = 2000
    temperature: float = 0.1

    @property
    def system_prompt(self) -> str:
        return (
            "أنت متخصص في تراخيص وزارة الصحة السعودية ومتطلبات اعتماد CBAHI.\n\n"
            "You are an MOH (Saudi Ministry of Health) licensing specialist with "
            "deep knowledge of facility licensing requirements and CBAHI accreditation.\n\n"
            "Your responsibilities:\n"
            "- Look up MOH facility license types (hospital, clinic, pharmacy, lab, etc.).\n"
            "- Identify licensing fees, requirements, and processing timelines.\n"
            "- Check CBAHI accreditation requirements for healthcare facilities.\n"
            "- Flag mandatory staffing ratios and compliance obligations.\n"
            "- All monetary values in SAR.\n"
            "- Return a JSON object with: moh_licenses, cbahi_requirements, compliance_flags.\n"
            "  No text outside the JSON block."
        )

    @property
    def tools(self) -> list:
        return [
            {
                "name": "lookup_moh_license",
                "description": (
                    "Looks up MOH facility license types for a given healthcare facility type. "
                    "Returns license requirements, fees, staffing minimums, and processing timeline."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "facility_type": {
                            "type": "string",
                            "description": "Type of healthcare facility (e.g. hospital, clinic, pharmacy, lab, dental_clinic)",
                        },
                    },
                    "required": ["facility_type"],
                },
            },
            {
                "name": "check_cbahi_requirements",
                "description": (
                    "Returns CBAHI (Saudi Central Board for Accreditation of Healthcare "
                    "Institutions) accreditation requirements, standards, and compliance checklist."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        ]

    def execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        if tool_name == "lookup_moh_license":
            facility_type = tool_input.get("facility_type", "clinic")
            return self._lookup_moh_license(facility_type)
        if tool_name == "check_cbahi_requirements":
            return self._check_cbahi_requirements()
        raise NotImplementedError(f"Unknown tool: {tool_name}")

    def _lookup_moh_license(self, facility_type: str) -> dict:
        all_licenses = get_moh_licenses()
        facility_lower = facility_type.lower().strip()

        # Try to find matching license(s)
        matched = []
        for lic in all_licenses:
            lic_type = lic.get("type", lic.get("facility_type", "")).lower()
            lic_name = lic.get("name", lic.get("name_en", "")).lower()
            if facility_lower in lic_type or facility_lower in lic_name:
                matched.append(lic)

        if not matched:
            return {
                "facility_type": facility_type,
                "status": "not_found",
                "all_licenses": all_licenses,
                "message": (
                    f"No exact match for '{facility_type}'. "
                    "Returning all available license types for reference."
                ),
            }

        return {
            "facility_type": facility_type,
            "status": "found",
            "licenses": matched,
        }

    def _check_cbahi_requirements(self) -> dict:
        return get_cbahi_requirements()
