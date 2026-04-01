"""
DataComplianceSubAgent — checks Saudi data localization rules (NDMO),
PDPL compliance requirements, and e-commerce regulations.
"""

from typing import Any

from app.agents.base_agent import BaseAgent
from app.services.data_tools import (
    get_data_localization_rules,
    get_pdpl_requirements,
    get_ecommerce_regs,
)


class DataComplianceSubAgent(BaseAgent):
    name: str = "DataComplianceSubAgent"
    description: str = "Saudi data privacy and compliance checks (NDMO, PDPL, NCA)"
    max_tokens: int = 2000
    temperature: float = 0.1

    @property
    def system_prompt(self) -> str:
        return (
            "أنت متخصص في خصوصية البيانات والامتثال في المملكة العربية السعودية "
            "(NDMO، PDPL، NCA).\n\n"
            "You are a Saudi data privacy and compliance specialist with expertise in:\n"
            "- NDMO (National Data Management Office) data localization rules.\n"
            "- PDPL (Personal Data Protection Law) compliance requirements.\n"
            "- NCA (National Cybersecurity Authority) standards.\n"
            "- E-commerce regulations and consumer protection.\n\n"
            "Your responsibilities:\n"
            "- Check data localization requirements by data type.\n"
            "- Identify PDPL obligations for data controllers and processors.\n"
            "- Flag e-commerce compliance requirements where applicable.\n"
            "- All monetary values in SAR.\n"
            "- Return a JSON object with: data_localization, pdpl_compliance, "
            "  ecommerce_requirements.\n"
            "  No text outside the JSON block."
        )

    @property
    def tools(self) -> list:
        return [
            {
                "name": "check_data_localization",
                "description": (
                    "Checks NDMO data localization requirements for a given data type. "
                    "Returns hosting rules, cross-border transfer restrictions, and "
                    "compliance obligations."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "data_type": {
                            "type": "string",
                            "description": (
                                "Type of data to check localization rules for "
                                "(e.g. 'personal', 'financial', 'health', 'government')"
                            ),
                        },
                    },
                    "required": [],
                },
            },
            {
                "name": "get_pdpl_requirements_data",
                "description": (
                    "Returns PDPL (Personal Data Protection Law) requirements including "
                    "consent rules, data subject rights, breach notification, and penalties."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
            {
                "name": "check_ecommerce_regs",
                "description": (
                    "Returns e-commerce regulations including consumer protection, "
                    "return policies, and online business registration requirements."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        ]

    def execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        if tool_name == "check_data_localization":
            return self._check_data_localization(tool_input)
        if tool_name == "get_pdpl_requirements_data":
            return self._get_pdpl_requirements_data()
        if tool_name == "check_ecommerce_regs":
            return self._check_ecommerce_regs()
        raise NotImplementedError(f"Unknown tool: {tool_name}")

    def _check_data_localization(self, tool_input: dict) -> dict:
        data_type = tool_input.get("data_type", "")
        rules = get_data_localization_rules()
        if not data_type:
            return rules
        # If the rules dict has per-type entries, try to filter
        keyword = data_type.lower()
        if isinstance(rules, dict):
            filtered = {
                k: v
                for k, v in rules.items()
                if keyword in str(k).lower() or keyword in str(v).lower()
            }
            return filtered if filtered else rules
        return rules

    def _get_pdpl_requirements_data(self) -> dict:
        return get_pdpl_requirements()

    def _check_ecommerce_regs(self) -> dict:
        return get_ecommerce_regs()
