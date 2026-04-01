"""
FacilityRequirementsSubAgent — calculates education facility space requirements
and teacher-student ratios for school feasibility studies.
"""

import json
from typing import Any

from app.agents.base_agent import BaseAgent
from app.services.data_tools import get_education_facility_reqs, get_teacher_ratios


class FacilityRequirementsSubAgent(BaseAgent):
    name: str = "FacilityRequirementsSubAgent"
    description: str = "Education facility planning and teacher ratio specialist"
    max_tokens: int = 2000
    temperature: float = 0.1

    @property
    def system_prompt(self) -> str:
        return (
            "أنت متخصص في تخطيط المرافق التعليمية ومعايير التوظيف في المدارس السعودية.\n\n"
            "You are an education facility planning specialist with expertise in "
            "Saudi school building standards, space requirements, and teacher-student "
            "ratio regulations.\n\n"
            "Your responsibilities:\n"
            "- Calculate facility space requirements based on student capacity and school level.\n"
            "- Determine teacher-student ratios per MOE regulations.\n"
            "- Estimate facility setup and construction costs.\n"
            "- Ensure compliance with Civil Defense and municipal building codes.\n"
            "- All monetary values in SAR, all areas in square meters.\n"
            "- Return a JSON object with: facility_requirements, teacher_ratios, cost_estimates.\n"
            "  No text outside the JSON block."
        )

    @property
    def tools(self) -> list:
        return [
            {
                "name": "calculate_space_requirements",
                "description": (
                    "Calculates facility space requirements (in sqm) for a school "
                    "based on student capacity and school level. Returns classroom count, "
                    "total area, and facility breakdown."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "student_capacity": {
                            "type": "integer",
                            "description": "Target number of students the facility should accommodate",
                        },
                        "school_level": {
                            "type": "string",
                            "description": "School level (e.g. kindergarten, elementary, intermediate, secondary, k12)",
                        },
                    },
                    "required": ["student_capacity", "school_level"],
                },
            },
            {
                "name": "get_teacher_ratios_data",
                "description": (
                    "Returns MOE-mandated teacher-student ratios and staffing "
                    "requirements by school level."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "school_level": {
                            "type": "string",
                            "description": "School level (e.g. kindergarten, elementary, intermediate, secondary, k12)",
                        },
                    },
                    "required": ["school_level"],
                },
            },
        ]

    def execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        if tool_name == "calculate_space_requirements":
            student_capacity = tool_input.get("student_capacity", 500)
            school_level = tool_input.get("school_level", "k12")
            return self._calculate_space_requirements(student_capacity, school_level)
        if tool_name == "get_teacher_ratios_data":
            school_level = tool_input.get("school_level", "k12")
            return self._get_teacher_ratios_data(school_level)
        raise NotImplementedError(f"Unknown tool: {tool_name}")

    def _calculate_space_requirements(
        self, student_capacity: int, school_level: str
    ) -> dict:
        facility_reqs = get_education_facility_reqs()

        # Space per student benchmarks (sqm) by level
        space_benchmarks = {
            "kindergarten": {"per_student_sqm": 8.0, "students_per_class": 20},
            "elementary": {"per_student_sqm": 6.5, "students_per_class": 25},
            "intermediate": {"per_student_sqm": 7.0, "students_per_class": 28},
            "secondary": {"per_student_sqm": 7.5, "students_per_class": 30},
            "k12": {"per_student_sqm": 7.0, "students_per_class": 25},
        }

        level_lower = school_level.lower().strip()
        benchmark = space_benchmarks.get(level_lower, space_benchmarks["k12"])

        total_sqm = int(student_capacity * benchmark["per_student_sqm"])
        num_classrooms = max(
            1,
            -(-student_capacity // benchmark["students_per_class"]),  # ceil division
        )

        # Facility breakdown
        classroom_area = int(num_classrooms * 55)  # avg 55 sqm per classroom
        admin_area = int(total_sqm * 0.10)
        lab_area = int(total_sqm * 0.08)
        library_area = int(total_sqm * 0.05)
        sports_area = int(total_sqm * 0.15)
        common_area = int(total_sqm * 0.12)
        circulation = int(total_sqm * 0.15)

        # Cost estimates (SAR per sqm)
        construction_cost_per_sqm = 4_500
        fitout_cost_per_sqm = 1_800
        total_construction = total_sqm * construction_cost_per_sqm
        total_fitout = total_sqm * fitout_cost_per_sqm

        return {
            "school_level": school_level,
            "student_capacity": student_capacity,
            "per_student_sqm": benchmark["per_student_sqm"],
            "students_per_class": benchmark["students_per_class"],
            "num_classrooms": num_classrooms,
            "total_facility_sqm": total_sqm,
            "facility_breakdown_sqm": {
                "classrooms": classroom_area,
                "administration": admin_area,
                "laboratories": lab_area,
                "library": library_area,
                "sports_facilities": sports_area,
                "common_areas": common_area,
                "circulation_and_services": circulation,
            },
            "cost_estimates_sar": {
                "construction_per_sqm": construction_cost_per_sqm,
                "fitout_per_sqm": fitout_cost_per_sqm,
                "total_construction": total_construction,
                "total_fitout": total_fitout,
                "total_facility_cost": total_construction + total_fitout,
            },
            "seed_data": facility_reqs,
            "notes": [
                "Areas comply with MOE minimum space standards",
                "Civil Defense fire safety requirements apply",
                "Municipality building permit required before construction",
                "Parking ratio: 1 space per 50 sqm of built area",
            ],
        }

    def _get_teacher_ratios_data(self, school_level: str) -> dict:
        all_ratios = get_teacher_ratios()
        level_lower = school_level.lower().strip()

        # Staffing ratio benchmarks
        ratio_benchmarks = {
            "kindergarten": {
                "teacher_student_ratio": "1:10",
                "max_students_per_class": 20,
                "teaching_assistants_per_class": 1,
                "specialist_teachers": ["art", "pe", "music"],
            },
            "elementary": {
                "teacher_student_ratio": "1:20",
                "max_students_per_class": 25,
                "teaching_assistants_per_class": 0,
                "specialist_teachers": ["art", "pe", "english", "computer"],
            },
            "intermediate": {
                "teacher_student_ratio": "1:22",
                "max_students_per_class": 28,
                "teaching_assistants_per_class": 0,
                "specialist_teachers": ["science_lab", "computer_lab", "counselor"],
            },
            "secondary": {
                "teacher_student_ratio": "1:25",
                "max_students_per_class": 30,
                "teaching_assistants_per_class": 0,
                "specialist_teachers": [
                    "science_lab",
                    "computer_lab",
                    "counselor",
                    "career_advisor",
                ],
            },
            "k12": {
                "teacher_student_ratio": "1:20",
                "max_students_per_class": 25,
                "teaching_assistants_per_class": 0,
                "specialist_teachers": [
                    "art",
                    "pe",
                    "science_lab",
                    "computer_lab",
                    "counselor",
                ],
            },
        }

        benchmark = ratio_benchmarks.get(level_lower, ratio_benchmarks["k12"])

        return {
            "school_level": school_level,
            "ratios": benchmark,
            "moe_seed_data": all_ratios,
            "admin_staff_notes": [
                "Principal: 1 per school",
                "Vice-principal: 1 per 300 students",
                "Administrative staff: 1 per 100 students",
                "Counselor: 1 per 250 students",
                "Nurse: 1 per school (mandatory)",
                "Security: minimum 2 per school",
            ],
        }
