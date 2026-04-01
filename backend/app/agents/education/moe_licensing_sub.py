"""
MOELicensingSubAgent — looks up MOE school/institute types and curriculum
requirements for education feasibility studies.
"""

import json
from typing import Any

from app.agents.base_agent import BaseAgent
from app.services.data_tools import get_moe_school_types, get_moe_curriculum_reqs


class MOELicensingSubAgent(BaseAgent):
    name: str = "MOELicensingSubAgent"
    description: str = "MOE licensing and curriculum requirements specialist"
    max_tokens: int = 2000
    temperature: float = 0.1

    @property
    def system_prompt(self) -> str:
        return (
            "أنت متخصص في تراخيص وزارة التعليم السعودية ومتطلبات المناهج الدراسية.\n\n"
            "You are an MOE (Saudi Ministry of Education) licensing specialist with "
            "deep knowledge of school licensing requirements, curriculum accreditation, "
            "and regulatory compliance for private education in Saudi Arabia.\n\n"
            "Your responsibilities:\n"
            "- Look up MOE school/institute license types and requirements.\n"
            "- Identify curriculum requirements for different school types.\n"
            "- Detail licensing fees, processing timelines, and renewal obligations.\n"
            "- Flag mandatory Arabic language and Islamic studies requirements.\n"
            "- All monetary values in SAR.\n"
            "- Return a JSON object with: moe_license_details, curriculum_requirements, "
            "compliance_flags.\n"
            "  No text outside the JSON block."
        )

    @property
    def tools(self) -> list:
        return [
            {
                "name": "lookup_moe_license",
                "description": (
                    "Looks up MOE school/institute license types for a given school type. "
                    "Returns license requirements, fees, and processing timeline."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "school_type": {
                            "type": "string",
                            "description": "Type of school (e.g. international_school, private_school, training_institute, kindergarten)",
                        },
                    },
                    "required": ["school_type"],
                },
            },
            {
                "name": "check_curriculum_requirements",
                "description": (
                    "Returns MOE curriculum requirements for a given curriculum type "
                    "including mandatory subjects, teaching hours, and accreditation standards."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "curriculum_type": {
                            "type": "string",
                            "description": "Curriculum type (e.g. international, national, american, british, ib)",
                        },
                    },
                    "required": ["curriculum_type"],
                },
            },
        ]

    def execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        if tool_name == "lookup_moe_license":
            school_type = tool_input.get("school_type", "international_school")
            return self._lookup_moe_license(school_type)
        if tool_name == "check_curriculum_requirements":
            curriculum_type = tool_input.get("curriculum_type", "international")
            return self._check_curriculum_requirements(curriculum_type)
        raise NotImplementedError(f"Unknown tool: {tool_name}")

    def _lookup_moe_license(self, school_type: str) -> dict:
        all_types = get_moe_school_types()
        school_lower = school_type.lower().strip()

        matched = []
        for st in all_types:
            st_type = st.get("type", st.get("school_type", "")).lower()
            st_name = st.get("name", st.get("name_en", "")).lower()
            if school_lower in st_type or school_lower in st_name:
                matched.append(st)

        if not matched:
            return {
                "school_type": school_type,
                "status": "not_found",
                "all_school_types": all_types,
                "message": (
                    f"No exact match for '{school_type}'. "
                    "Returning all available school types for reference."
                ),
            }

        return {
            "school_type": school_type,
            "status": "found",
            "license_details": matched,
        }

    def _check_curriculum_requirements(self, curriculum_type: str) -> dict:
        all_reqs = get_moe_curriculum_reqs()
        curriculum_lower = curriculum_type.lower().strip()

        # Try to find matching curriculum
        if isinstance(all_reqs, dict):
            matched = {}
            for key, value in all_reqs.items():
                if curriculum_lower in key.lower():
                    matched[key] = value

            if matched:
                return {
                    "curriculum_type": curriculum_type,
                    "status": "found",
                    "requirements": matched,
                }

        return {
            "curriculum_type": curriculum_type,
            "status": "reference",
            "all_requirements": all_reqs,
            "message": (
                f"Returning all curriculum requirements. "
                f"Filter for '{curriculum_type}' as needed."
            ),
        }
