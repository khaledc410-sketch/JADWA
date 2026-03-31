"""
SMEProgramsSubAgent — Monsha'at programs, eligibility, SME benefits,
and sector regulator information.
"""

from typing import Any

from app.agents.base_agent import BaseAgent
from app.services.data_tools import get_incentive_programs, load_seed


# Sector-to-regulator mapping (ported from original LegalRegulatoryAgent)
_SECTOR_REGULATORS = {
    "food_beverage": {
        "regulator": "SFDA",
        "regulator_ar": "هيئة الغذاء والدواء",
        "license_name_en": "Food Establishment License",
        "license_name_ar": "رخصة منشأة غذائية",
        "cost_sar": 5_000,
        "timeline_days": 30,
        "annual_renewal_sar": 2_500,
        "requirements": [
            "Kitchen layout approval",
            "Food handler health cards",
            "HACCP plan",
        ],
    },
    "healthcare": {
        "regulator": "MOH",
        "regulator_ar": "وزارة الصحة",
        "license_name_en": "Private Health Facility License",
        "license_name_ar": "رخصة منشأة صحية خاصة",
        "cost_sar": 15_000,
        "timeline_days": 90,
        "annual_renewal_sar": 5_000,
        "requirements": [
            "Building compliance certificate",
            "Equipment list approval",
            "Staff credentials",
        ],
    },
    "real_estate": {
        "regulator": "REGA",
        "regulator_ar": "الهيئة العامة للعقارات",
        "license_name_en": "Real Estate Development License",
        "license_name_ar": "ترخيص تطوير عقاري",
        "cost_sar": 12_000,
        "timeline_days": 45,
        "annual_renewal_sar": 6_000,
        "requirements": [
            "Land ownership documents",
            "Architectural drawings",
            "Environmental clearance",
        ],
    },
    "technology": {
        "regulator": "CITC",
        "regulator_ar": "هيئة الاتصالات وتقنية المعلومات",
        "license_name_en": "CITC Service Provider License",
        "license_name_ar": "ترخيص مزود خدمة",
        "cost_sar": 10_000,
        "timeline_days": 45,
        "annual_renewal_sar": 4_000,
        "requirements": [
            "Data localization compliance",
            "Cybersecurity policy",
            "CR required first",
        ],
    },
    "education": {
        "regulator": "MOE",
        "regulator_ar": "وزارة التعليم",
        "license_name_en": "Private Education Institution License",
        "license_name_ar": "ترخيص مؤسسة تعليمية خاصة",
        "cost_sar": 8_000,
        "timeline_days": 60,
        "annual_renewal_sar": 4_000,
        "requirements": [
            "Curriculum approval",
            "Building safety certificate",
            "Teacher credentials",
        ],
    },
    "franchise": {
        "regulator": "RFTA / MCI",
        "regulator_ar": "نظام الامتياز التجاري",
        "license_name_en": "Franchise Disclosure Document Filing",
        "license_name_ar": "إيداع وثيقة الإفصاح عن الامتياز",
        "cost_sar": 5_000,
        "timeline_days": 30,
        "annual_renewal_sar": 2_000,
        "requirements": [
            "Franchise Disclosure Document (FDD)",
            "Franchisor CR copy",
            "Territory agreement",
        ],
    },
}

_DEFAULT_REGULATOR = {
    "regulator": "MCI",
    "regulator_ar": "وزارة التجارة",
    "license_name_en": "General Commercial License",
    "license_name_ar": "رخصة تجارية عامة",
    "cost_sar": 1_200,
    "timeline_days": 3,
    "annual_renewal_sar": 600,
    "requirements": ["Valid CR", "Municipality approval"],
}


class SMEProgramsSubAgent(BaseAgent):
    name: str = "SMEProgramsSubAgent"
    description: str = (
        "Monsha'at SME programs, HRDF support, Kafalah loans, "
        "eligibility criteria, and sector regulator information"
    )
    temperature: float = 0.2

    @property
    def system_prompt(self) -> str:
        return (
            "أنت متخصص في منظومة دعم المنشآت الصغيرة والمتوسطة في المملكة العربية السعودية.\n\n"
            "You are a Saudi SME ecosystem specialist covering:\n"
            "- Monsha'at (منشآت): SME registration, support programs, digital grants\n"
            "- HRDF (صندوق تنمية الموارد البشرية): Saudization support, training subsidies\n"
            "- Kafalah (كفالة): SME loan guarantee program\n"
            "- Government procurement access (منصة اعتماد)\n"
            "- Sector-specific regulators and their requirements\n\n"
            "For SME programs:\n"
            "- List available programs with eligibility criteria.\n"
            "- Provide loan amounts, grant values in SAR.\n"
            "- Categorize business size: micro (<500K), small (<5M), medium (<50M).\n"
            "For sector regulators:\n"
            "- Identify the primary regulator for the sector.\n"
            "- List license costs, timelines, and renewal fees.\n\n"
            "Return JSON with: monshaat_programs, sector_regulator, "
            "size_category, eligibility_summary."
        )

    @property
    def tools(self) -> list:
        return [
            {
                "name": "fetch_monshaat_requirements",
                "description": (
                    "Fetches Monsha'at SME registration requirements, eligibility criteria, "
                    "and available support programs including loans, grants, and advisory services."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sector": {
                            "type": "string",
                            "description": "Business sector",
                        },
                        "investment_sar": {
                            "type": "number",
                            "description": "Planned investment amount in SAR for size classification",
                        },
                    },
                    "required": ["sector"],
                },
            },
            {
                "name": "get_sector_regulator",
                "description": (
                    "Returns the primary sector regulator, license requirements, "
                    "costs, timelines, and renewal fees for the given sector."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sector": {
                            "type": "string",
                            "description": "Business sector (e.g. food_beverage, healthcare, technology)",
                        },
                    },
                    "required": ["sector"],
                },
            },
        ]

    def execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        if tool_name == "fetch_monshaat_requirements":
            return self._fetch_monshaat_requirements(**tool_input)
        if tool_name == "get_sector_regulator":
            return self._get_sector_regulator(**tool_input)
        raise NotImplementedError(f"Unknown tool: {tool_name}")

    def _fetch_monshaat_requirements(
        self, sector: str, investment_sar: float = 0
    ) -> dict:
        # Pull any matching incentive programs from seed data
        programs = get_incentive_programs(sector)

        size_category = (
            "micro"
            if investment_sar < 500_000
            else "small"
            if investment_sar < 5_000_000
            else "medium"
        )

        return {
            "monshaat_eligible": True,
            "registration_cost_sar": 0,
            "registration_days": 1,
            "size_category": size_category,
            "benefits": [
                "Access to government procurement (منصة اعتماد)",
                "Monsha'at loans up to SAR 3M (قروض منشآت)",
                "Free business advisory services",
                "Saudization (نطاقات) compliance support",
                "Digital transformation grants up to SAR 250,000",
            ],
            "incentive_programs": programs,
            "url": "https://monshaat.gov.sa",
        }

    def _get_sector_regulator(self, sector: str) -> dict:
        return _SECTOR_REGULATORS.get(sector.lower(), _DEFAULT_REGULATOR)

    def _build_user_message(self, context: dict) -> str:
        sector = context.get("sector", "default")
        investment = context.get(
            "investment_sar", context.get("total_investment_sar", 0)
        )
        return (
            f"Identify SME programs and sector regulator for this business.\n"
            f"Sector: {sector} | Investment: SAR {investment:,.0f}\n\n"
            f"Steps:\n"
            f"1. Call fetch_monshaat_requirements with sector '{sector}' "
            f"and investment_sar {investment}.\n"
            f"2. Call get_sector_regulator with sector '{sector}'.\n\n"
            f"Return JSON with: monshaat_programs, sector_regulator, "
            f"size_category, eligibility_summary."
        )
