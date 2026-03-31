"""
IntakeValidationAgent — validates and normalizes user intake form data.
Assigns a completeness score (0-100) and surfaces errors/warnings.
"""

import json
import re
from typing import Any

from app.agents.base_agent import BaseAgent


VALID_SECTORS = [
    "retail",
    "food_beverage",
    "healthcare",
    "education",
    "technology",
    "real_estate",
    "manufacturing",
    "logistics",
    "hospitality",
    "franchise",
    "consulting",
    "construction",
    "agriculture",
    "energy",
    "finance",
]

SAUDI_REGIONS = [
    "riyadh",
    "makkah",
    "madinah",
    "eastern_province",
    "asir",
    "tabuk",
    "hail",
    "northern_borders",
    "jazan",
    "najran",
    "al_bahah",
    "al_jouf",
    "qassim",
]

SAUDI_CITIES = [
    "riyadh",
    "jeddah",
    "mecca",
    "medina",
    "dammam",
    "khobar",
    "dhahran",
    "jubail",
    "yanbu",
    "taif",
    "tabuk",
    "abha",
    "khamis_mushait",
    "buraidah",
    "hail",
    "najran",
    "jizan",
    "sakaka",
]


class IntakeValidationAgent(BaseAgent):
    name: str = "IntakeValidationAgent"
    description: str = "Validates and normalizes Saudi business intake form data"

    @property
    def system_prompt(self) -> str:
        return (
            "You are an expert Saudi business analyst specializing in validating new "
            "business intake forms for the Kingdom of Saudi Arabia. Your role is to:\n"
            "1. Check that all required fields are present and correctly filled.\n"
            "2. Normalize data (e.g., city names, sector codes, investment amounts).\n"
            "3. Identify missing or inconsistent information.\n"
            "4. Assign a completeness score from 0 to 100.\n"
            "5. Surface warnings for fields that are present but may be unrealistic "
            "   (e.g., investment amount too low for the chosen sector in Saudi Arabia).\n\n"
            "Always respond with a JSON object matching the output schema. "
            "Use both Arabic and English for user-facing messages. "
            "Be conservative: flag ambiguities rather than silently fixing them."
        )

    @property
    def tools(self) -> list:
        return [
            {
                "name": "validate_business_name",
                "description": (
                    "Checks whether the proposed business name complies with Saudi MCI "
                    "naming rules (no offensive terms, no misleading sector claims, "
                    "length constraints). Returns validation status and suggested alternatives."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "business_name": {
                            "type": "string",
                            "description": "The proposed Arabic or English business name",
                        },
                        "sector": {
                            "type": "string",
                            "description": "Business sector code",
                        },
                    },
                    "required": ["business_name"],
                },
            },
            {
                "name": "check_sector_eligibility",
                "description": (
                    "Verifies whether a given investor nationality / ownership structure "
                    "is eligible to operate in the specified sector under Saudi regulations "
                    "(foreign ownership restrictions, negative list, etc.)."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sector": {"type": "string", "description": "Sector code"},
                        "investor_nationality": {
                            "type": "string",
                            "description": "ISO country code of the investor",
                        },
                        "ownership_type": {
                            "type": "string",
                            "description": "sole_proprietorship | llc | joint_venture | foreign_branch",
                        },
                    },
                    "required": ["sector"],
                },
            },
            {
                "name": "normalize_location_data",
                "description": (
                    "Normalizes city and region names to canonical Saudi administrative "
                    "codes, returns GPS bounding box, population, and cost-of-living index."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string"},
                        "region": {"type": "string"},
                        "district": {"type": "string"},
                    },
                    "required": ["city"],
                },
            },
        ]

    # ------------------------------------------------------------------
    # Tool implementations
    # ------------------------------------------------------------------

    def execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        if tool_name == "validate_business_name":
            return self._validate_business_name(**tool_input)
        if tool_name == "check_sector_eligibility":
            return self._check_sector_eligibility(**tool_input)
        if tool_name == "normalize_location_data":
            return self._normalize_location_data(**tool_input)
        raise NotImplementedError(f"Unknown tool: {tool_name}")

    def _validate_business_name(self, business_name: str, sector: str = "") -> dict:
        errors = []
        warnings = []

        if len(business_name.strip()) < 3:
            errors.append("Business name is too short (minimum 3 characters).")
        if len(business_name.strip()) > 100:
            errors.append("Business name exceeds 100-character MCI limit.")

        forbidden_words = [
            "bank",
            "بنك",
            "government",
            "حكومة",
            "royal",
            "ملكي",
            "saudi aramco",
        ]
        for word in forbidden_words:
            if word.lower() in business_name.lower():
                errors.append(
                    f"The word '{word}' is restricted under MCI naming rules."
                )

        # Warn if name doesn't hint at the sector
        if sector and sector not in business_name.lower():
            warnings.append(
                "Consider including a sector-relevant keyword to aid brand clarity."
            )

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "mci_compliant": len(errors) == 0,
            "suggested_alternatives": [],
        }

    def _check_sector_eligibility(
        self,
        sector: str,
        investor_nationality: str = "SA",
        ownership_type: str = "llc",
    ) -> dict:
        # Sectors with foreign ownership restrictions in Saudi Arabia
        restricted_sectors = {
            "real_estate": {
                "min_capital_sar": 30_000_000,
                "note": "Real estate development for non-Saudis requires MISA licence.",
            },
            "retail": {
                "min_capital_sar": 26_000_000,
                "note": "100% foreign-owned retail allowed with minimum SAR 26M capital.",
            },
            "food_beverage": {
                "min_capital_sar": 1_000_000,
                "note": "Foreign investment in F&B permitted with MISA approval.",
            },
        }

        is_saudi = investor_nationality.upper() == "SA"
        restriction = restricted_sectors.get(sector, {})

        eligible = True
        flags = []
        if not is_saudi and restriction:
            flags.append(restriction.get("note", ""))

        return {
            "eligible": eligible,
            "sector": sector,
            "investor_nationality": investor_nationality,
            "ownership_type": ownership_type,
            "requires_misa_licence": not is_saudi and bool(restriction),
            "min_capital_sar": restriction.get("min_capital_sar", 0),
            "compliance_flags": flags,
        }

    def _normalize_location_data(
        self, city: str, region: str = "", district: str = ""
    ) -> dict:
        city_db = {
            "riyadh": {
                "name_ar": "الرياض",
                "region": "riyadh",
                "population": 7_500_000,
                "col_index": 100,
            },
            "jeddah": {
                "name_ar": "جدة",
                "region": "makkah",
                "population": 4_700_000,
                "col_index": 115,
            },
            "dammam": {
                "name_ar": "الدمام",
                "region": "eastern_province",
                "population": 1_200_000,
                "col_index": 108,
            },
            "mecca": {
                "name_ar": "مكة المكرمة",
                "region": "makkah",
                "population": 2_000_000,
                "col_index": 118,
            },
            "medina": {
                "name_ar": "المدينة المنورة",
                "region": "madinah",
                "population": 1_300_000,
                "col_index": 105,
            },
            "khobar": {
                "name_ar": "الخبر",
                "region": "eastern_province",
                "population": 400_000,
                "col_index": 110,
            },
            "abha": {
                "name_ar": "أبها",
                "region": "asir",
                "population": 300_000,
                "col_index": 85,
            },
            "tabuk": {
                "name_ar": "تبوك",
                "region": "tabuk",
                "population": 550_000,
                "col_index": 90,
            },
        }

        key = city.lower().replace(" ", "_").replace("-", "_")
        data = city_db.get(
            key,
            {
                "name_ar": city,
                "region": region or "unknown",
                "population": 0,
                "col_index": 100,
            },
        )

        return {
            "canonical_city": key,
            "city_name_ar": data["name_ar"],
            "city_name_en": key.replace("_", " ").title(),
            "region": data["region"],
            "district": district,
            "population": data["population"],
            "cost_of_living_index": data["col_index"],
            "normalized": True,
        }

    # ------------------------------------------------------------------
    # Custom user message builder
    # ------------------------------------------------------------------

    def _build_user_message(self, context: dict) -> str:
        return (
            "Please validate the following Saudi business intake form data.\n"
            "Use the available tools to check the business name, sector eligibility, "
            "and normalize the location data.\n"
            "After running all tools, return a JSON object with keys: "
            "validated_context, validation_errors, completeness_score, warnings.\n\n"
            f"Intake Form Data:\n{json.dumps(context, ensure_ascii=False, indent=2)}"
        )
