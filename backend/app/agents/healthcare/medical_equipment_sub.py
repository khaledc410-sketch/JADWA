"""
MedicalEquipmentSubAgent — looks up SFDA medical device regulations and
estimates equipment costs for healthcare facility setup.
"""

import json
from typing import Any

from app.agents.base_agent import BaseAgent
from app.services.data_tools import get_medical_device_regs


class MedicalEquipmentSubAgent(BaseAgent):
    name: str = "MedicalEquipmentSubAgent"
    description: str = "SFDA medical device regulation and equipment cost specialist"
    max_tokens: int = 2000
    temperature: float = 0.1

    @property
    def system_prompt(self) -> str:
        return (
            "أنت متخصص في تنظيمات الأجهزة الطبية لدى الهيئة العامة للغذاء والدواء (SFDA).\n\n"
            "You are an SFDA (Saudi Food and Drug Authority) medical device regulation "
            "specialist with expertise in device classification, import requirements, "
            "and equipment procurement for healthcare facilities.\n\n"
            "Your responsibilities:\n"
            "- Look up SFDA device classifications and import regulations.\n"
            "- Estimate medical equipment costs by facility type.\n"
            "- Identify mandatory registration and compliance requirements.\n"
            "- All monetary values in SAR.\n"
            "- Return a JSON object with: sfda_regulations, equipment_costs, compliance_notes.\n"
            "  No text outside the JSON block."
        )

    @property
    def tools(self) -> list:
        return [
            {
                "name": "lookup_sfda_device_regs",
                "description": (
                    "Looks up SFDA medical device regulations by device class "
                    "(Class I, II, III, IV). Returns registration requirements, "
                    "import rules, and compliance obligations."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "device_class": {
                            "type": "string",
                            "description": "SFDA device classification (e.g. I, II, III, IV, or 'all')",
                        },
                    },
                    "required": ["device_class"],
                },
            },
            {
                "name": "estimate_equipment_costs",
                "description": (
                    "Estimates medical equipment procurement costs for a given "
                    "healthcare facility type. Returns itemized equipment list "
                    "with estimated costs in SAR."
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
        ]

    def execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        if tool_name == "lookup_sfda_device_regs":
            device_class = tool_input.get("device_class", "all")
            return self._lookup_sfda_device_regs(device_class)
        if tool_name == "estimate_equipment_costs":
            facility_type = tool_input.get("facility_type", "clinic")
            return self._estimate_equipment_costs(facility_type)
        raise NotImplementedError(f"Unknown tool: {tool_name}")

    def _lookup_sfda_device_regs(self, device_class: str) -> dict:
        all_regs = get_medical_device_regs()
        device_class_lower = device_class.lower().strip()

        if device_class_lower == "all":
            return {
                "device_class": "all",
                "regulations": all_regs,
            }

        matched = []
        for reg in all_regs:
            reg_class = str(reg.get("class", reg.get("device_class", ""))).lower()
            if device_class_lower in reg_class:
                matched.append(reg)

        if not matched:
            return {
                "device_class": device_class,
                "status": "not_found",
                "all_regulations": all_regs,
                "message": (
                    f"No exact match for device class '{device_class}'. "
                    "Returning all device regulations for reference."
                ),
            }

        return {
            "device_class": device_class,
            "status": "found",
            "regulations": matched,
        }

    def _estimate_equipment_costs(self, facility_type: str) -> dict:
        # Equipment cost benchmarks by facility type (SAR)
        equipment_budgets = {
            "hospital": {
                "basic_medical_equipment": 5_000_000,
                "diagnostic_imaging": 8_000_000,
                "surgical_equipment": 3_000_000,
                "icu_equipment": 2_500_000,
                "laboratory_equipment": 1_500_000,
                "pharmacy_systems": 500_000,
                "it_and_emr_systems": 1_200_000,
                "furniture_and_fixtures": 2_000_000,
            },
            "clinic": {
                "basic_medical_equipment": 800_000,
                "diagnostic_equipment": 500_000,
                "examination_furniture": 200_000,
                "it_and_emr_systems": 150_000,
                "pharmacy_dispensing": 100_000,
                "furniture_and_fixtures": 250_000,
            },
            "pharmacy": {
                "dispensing_systems": 300_000,
                "storage_and_refrigeration": 150_000,
                "pos_and_inventory_systems": 80_000,
                "furniture_and_fixtures": 100_000,
            },
            "lab": {
                "analytical_instruments": 2_000_000,
                "sample_processing": 500_000,
                "quality_control_equipment": 300_000,
                "lims_software": 200_000,
                "safety_equipment": 150_000,
                "furniture_and_fixtures": 200_000,
            },
            "dental_clinic": {
                "dental_chairs_and_units": 600_000,
                "x_ray_and_imaging": 350_000,
                "sterilization_equipment": 100_000,
                "hand_instruments": 150_000,
                "it_and_practice_mgmt": 100_000,
                "furniture_and_fixtures": 150_000,
            },
        }

        facility_lower = facility_type.lower().strip()
        budget = equipment_budgets.get(facility_lower, equipment_budgets["clinic"])

        total_cost = sum(budget.values())

        return {
            "facility_type": facility_type,
            "equipment_breakdown": budget,
            "total_equipment_cost_sar": total_cost,
            "notes": [
                "Costs are estimates based on Saudi market benchmarks",
                "All medical devices must be SFDA-registered before import",
                "Installation and commissioning typically add 10-15% to equipment costs",
                "Annual maintenance contracts average 8-12% of equipment value",
            ],
        }
