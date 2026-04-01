"""
CITCRegulationsSubAgent — looks up CITC license types and fintech sandbox
requirements for technology companies operating in Saudi Arabia.
"""

from typing import Any

from app.agents.base_agent import BaseAgent
from app.services.data_tools import get_citc_licenses, get_fintech_sandbox


class CITCRegulationsSubAgent(BaseAgent):
    name: str = "CITCRegulationsSubAgent"
    description: str = (
        "CITC licensing and fintech sandbox lookup for Saudi tech companies"
    )
    max_tokens: int = 2000
    temperature: float = 0.1

    @property
    def system_prompt(self) -> str:
        return (
            "أنت متخصص في تنظيمات هيئة الاتصالات وتقنية المعلومات (CITC) في المملكة العربية السعودية.\n\n"
            "You are a CITC (Communications, Space and Technology Commission) regulations "
            "specialist for Saudi technology companies.\n\n"
            "Your responsibilities:\n"
            "- Look up CITC license types required for technology and telecom businesses.\n"
            "- Check fintech sandbox eligibility and requirements from SAMA.\n"
            "- Identify applicable license categories based on the business activity.\n"
            "- Flag any compliance risks or missing licenses.\n"
            "- All monetary values in SAR.\n"
            "- Return a JSON object with: citc_licenses, fintech_sandbox_status.\n"
            "  No text outside the JSON block."
        )

    @property
    def tools(self) -> list:
        return [
            {
                "name": "lookup_citc_license",
                "description": (
                    "Looks up CITC license types for technology and telecom companies "
                    "in Saudi Arabia. Optionally filters by license_type keyword."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "license_type": {
                            "type": "string",
                            "description": (
                                "License type keyword to filter results "
                                "(e.g. 'ISP', 'cloud', 'telecom', 'data_center')"
                            ),
                        },
                    },
                    "required": [],
                },
            },
            {
                "name": "check_fintech_sandbox",
                "description": (
                    "Checks SAMA fintech sandbox eligibility and requirements. "
                    "Returns sandbox application process, fees, and conditions."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        ]

    def execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        if tool_name == "lookup_citc_license":
            return self._lookup_citc_license(tool_input)
        if tool_name == "check_fintech_sandbox":
            return self._check_fintech_sandbox()
        raise NotImplementedError(f"Unknown tool: {tool_name}")

    def _lookup_citc_license(self, tool_input: dict) -> list:
        license_type = tool_input.get("license_type", "")
        all_licenses = get_citc_licenses()
        if not license_type:
            return all_licenses
        keyword = license_type.lower()
        filtered = [
            lic
            for lic in all_licenses
            if keyword in str(lic.get("type", "")).lower()
            or keyword in str(lic.get("name", "")).lower()
            or keyword in str(lic.get("category", "")).lower()
            or keyword in str(lic.get("description", "")).lower()
        ]
        return filtered if filtered else all_licenses

    def _check_fintech_sandbox(self) -> dict:
        return get_fintech_sandbox()
