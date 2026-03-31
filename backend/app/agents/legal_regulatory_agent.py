"""
LegalRegulatoryAgent — identifies all Saudi licenses, permits, and regulatory
requirements with costs in SAR and realistic timelines.
"""

import json
from typing import Any

from app.agents.base_agent import BaseAgent


# ---------------------------------------------------------------------------
# Saudi license database (mock — real data from Beehive/Balady APIs later)
# ---------------------------------------------------------------------------

_MCI_LICENSES = {
    "retail": [
        {
            "name_ar": "السجل التجاري",
            "name_en": "Commercial Registration (CR)",
            "authority": "MCI (وزارة التجارة)",
            "cost_sar": 1_200,
            "timeline_days": 3,
            "required": True,
            "online": True,
            "url": "https://cr.mc.gov.sa",
        },
        {
            "name_ar": "رخصة بلدية - محل تجاري",
            "name_en": "Municipal Business License",
            "authority": "Balady (بلدي)",
            "cost_sar": 2_500,
            "timeline_days": 14,
            "required": True,
            "online": True,
            "url": "https://balady.gov.sa",
        },
        {
            "name_ar": "تسجيل ضريبة القيمة المضافة",
            "name_en": "VAT Registration",
            "authority": "ZATCA (هيئة الزكاة والضريبة والجمارك)",
            "cost_sar": 0,
            "timeline_days": 7,
            "required": True,
            "online": True,
            "url": "https://zatca.gov.sa",
        },
    ],
    "food_beverage": [
        {
            "name_ar": "السجل التجاري",
            "name_en": "Commercial Registration (CR)",
            "authority": "MCI",
            "cost_sar": 1_200,
            "timeline_days": 3,
            "required": True,
            "online": True,
        },
        {
            "name_ar": "رخصة مزاولة نشاط غذائي",
            "name_en": "Food Establishment License",
            "authority": "SFDA (هيئة الغذاء والدواء)",
            "cost_sar": 5_000,
            "timeline_days": 30,
            "required": True,
            "online": False,
        },
        {
            "name_ar": "رخصة بلدية - مطعم / كافيه",
            "name_en": "Municipality Restaurant License",
            "authority": "Balady (بلدي)",
            "cost_sar": 3_500,
            "timeline_days": 21,
            "required": True,
            "online": True,
        },
        {
            "name_ar": "شهادة صحة بيئية",
            "name_en": "Environmental Health Certificate",
            "authority": "MOH (وزارة الصحة)",
            "cost_sar": 800,
            "timeline_days": 14,
            "required": True,
            "online": False,
        },
        {
            "name_ar": "تسجيل ضريبة القيمة المضافة",
            "name_en": "VAT Registration",
            "authority": "ZATCA",
            "cost_sar": 0,
            "timeline_days": 7,
            "required": True,
            "online": True,
        },
    ],
    "healthcare": [
        {
            "name_ar": "السجل التجاري",
            "name_en": "Commercial Registration (CR)",
            "authority": "MCI",
            "cost_sar": 1_200,
            "timeline_days": 3,
            "required": True,
            "online": True,
        },
        {
            "name_ar": "ترخيص وزارة الصحة - منشأة صحية خاصة",
            "name_en": "MOH Private Health Facility License",
            "authority": "MOH (وزارة الصحة)",
            "cost_sar": 15_000,
            "timeline_days": 90,
            "required": True,
            "online": False,
        },
        {
            "name_ar": "اعتماد الهيئة السعودية للتخصصات الصحية",
            "name_en": "SCFHS Practitioner Accreditation",
            "authority": "SCFHS (الهيئة السعودية للتخصصات الصحية)",
            "cost_sar": 3_000,
            "timeline_days": 60,
            "required": True,
            "online": True,
        },
        {
            "name_ar": "رخصة بلدية",
            "name_en": "Municipality License",
            "authority": "Balady (بلدي)",
            "cost_sar": 2_500,
            "timeline_days": 14,
            "required": True,
            "online": True,
        },
    ],
    "technology": [
        {
            "name_ar": "السجل التجاري",
            "name_en": "Commercial Registration (CR)",
            "authority": "MCI",
            "cost_sar": 1_200,
            "timeline_days": 3,
            "required": True,
            "online": True,
        },
        {
            "name_ar": "تسجيل الملكية الفكرية",
            "name_en": "Intellectual Property Registration",
            "authority": "SAIP (هيئة الملكية الفكرية)",
            "cost_sar": 2_000,
            "timeline_days": 30,
            "required": False,
            "online": True,
        },
        {
            "name_ar": "ترخيص تقديم خدمات الاتصالات",
            "name_en": "Telecom Services License (if applicable)",
            "authority": "CITC (هيئة الاتصالات)",
            "cost_sar": 10_000,
            "timeline_days": 45,
            "required": False,
            "online": True,
        },
        {
            "name_ar": "تسجيل ضريبة القيمة المضافة",
            "name_en": "VAT Registration",
            "authority": "ZATCA",
            "cost_sar": 0,
            "timeline_days": 7,
            "required": True,
            "online": True,
        },
    ],
    "franchise": [
        {
            "name_ar": "السجل التجاري",
            "name_en": "Commercial Registration (CR)",
            "authority": "MCI",
            "cost_sar": 1_200,
            "timeline_days": 3,
            "required": True,
            "online": True,
        },
        {
            "name_ar": "تسجيل الامتياز التجاري - نظام الامتياز (RFTA)",
            "name_en": "Franchise Registration (RFTA)",
            "authority": "MCI / RFTA",
            "cost_sar": 5_000,
            "timeline_days": 30,
            "required": True,
            "online": True,
        },
        {
            "name_ar": "رخصة بلدية",
            "name_en": "Municipality License",
            "authority": "Balady (بلدي)",
            "cost_sar": 2_500,
            "timeline_days": 14,
            "required": True,
            "online": True,
        },
        {
            "name_ar": "تسجيل ضريبة القيمة المضافة",
            "name_en": "VAT Registration",
            "authority": "ZATCA",
            "cost_sar": 0,
            "timeline_days": 7,
            "required": True,
            "online": True,
        },
    ],
    "real_estate": [
        {
            "name_ar": "السجل التجاري",
            "name_en": "Commercial Registration (CR)",
            "authority": "MCI",
            "cost_sar": 1_200,
            "timeline_days": 3,
            "required": True,
            "online": True,
        },
        {
            "name_ar": "ترخيص الهيئة العامة للعقارات",
            "name_en": "Real Estate General Authority License",
            "authority": "REGA (الهيئة العامة للعقارات)",
            "cost_sar": 12_000,
            "timeline_days": 45,
            "required": True,
            "online": True,
        },
        {
            "name_ar": "رخصة البناء",
            "name_en": "Building Permit",
            "authority": "Balady (بلدي)",
            "cost_sar": 8_000,
            "timeline_days": 60,
            "required": True,
            "online": True,
        },
        {
            "name_ar": "تسجيل ضريبة القيمة المضافة",
            "name_en": "VAT Registration",
            "authority": "ZATCA",
            "cost_sar": 0,
            "timeline_days": 7,
            "required": True,
            "online": True,
        },
    ],
    "default": [
        {
            "name_ar": "السجل التجاري",
            "name_en": "Commercial Registration (CR)",
            "authority": "MCI",
            "cost_sar": 1_200,
            "timeline_days": 3,
            "required": True,
            "online": True,
        },
        {
            "name_ar": "رخصة بلدية",
            "name_en": "Municipality License",
            "authority": "Balady (بلدي)",
            "cost_sar": 2_500,
            "timeline_days": 14,
            "required": True,
            "online": True,
        },
        {
            "name_ar": "تسجيل ضريبة القيمة المضافة",
            "name_en": "VAT Registration",
            "authority": "ZATCA",
            "cost_sar": 0,
            "timeline_days": 7,
            "required": True,
            "online": True,
        },
    ],
}


class LegalRegulatoryAgent(BaseAgent):
    name: str = "LegalRegulatoryAgent"
    description: str = (
        "Saudi licenses, permits, regulatory requirements with costs and timelines"
    )
    temperature: float = 0.2

    @property
    def system_prompt(self) -> str:
        return (
            "أنت خبير قانوني وتنظيمي سعودي متخصص في متطلبات تأسيس الأعمال في المملكة العربية السعودية.\n\n"
            "You are a Saudi legal and regulatory expert covering:\n"
            "- MCI (وزارة التجارة): Commercial Registration, business licensing\n"
            "- Monsha'at (منشآت): SME support and registration\n"
            "- SFDA (هيئة الغذاء والدواء): Food, pharmaceutical, medical device licensing\n"
            "- REGA (الهيئة العامة للعقارات): Real estate development licensing\n"
            "- Balady (بلدي): Municipality permits\n"
            "- ZATCA (هيئة الزكاة والضريبة): VAT, Zakat registration\n"
            "- MOH, MOE, CITC: Sector-specific regulators\n\n"
            "For each license/permit:\n"
            "- Provide accurate cost estimates in SAR.\n"
            "- State realistic processing timelines in business days.\n"
            "- Flag compliance risks for foreign investors.\n"
            "- Provide both Arabic and English names and descriptions.\n"
            "Return a JSON object matching the output schema exactly."
        )

    @property
    def tools(self) -> list:
        return [
            {
                "name": "lookup_mci_licenses",
                "description": (
                    "Returns all MCI-required licenses and registrations for a given sector, "
                    "including Commercial Registration, sector-specific permits, and costs."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sector": {"type": "string"},
                        "ownership_type": {
                            "type": "string",
                            "description": "sole_proprietorship | llc | joint_venture | foreign_branch",
                        },
                    },
                    "required": ["sector"],
                },
            },
            {
                "name": "fetch_monshaat_requirements",
                "description": (
                    "Fetches Monsha'at SME registration requirements, eligibility criteria, "
                    "and available support programs for the business."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sector": {"type": "string"},
                        "investment_sar": {"type": "number"},
                    },
                    "required": ["sector"],
                },
            },
            {
                "name": "check_foreign_ownership_rules",
                "description": (
                    "Checks foreign ownership rules, MISA requirements, negative list sectors, "
                    "and minimum capital requirements for non-Saudi investors."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sector": {"type": "string"},
                        "investor_nationality": {"type": "string"},
                    },
                    "required": ["sector"],
                },
            },
            {
                "name": "get_sector_regulator_requirements",
                "description": (
                    "Returns requirements from the primary sector regulator "
                    "(SFDA for food/health, REGA for real estate, MOH for healthcare, etc.)."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sector": {"type": "string"},
                        "city": {"type": "string"},
                    },
                    "required": ["sector"],
                },
            },
        ]

    # ------------------------------------------------------------------
    # Tool implementations
    # ------------------------------------------------------------------

    def execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        if tool_name == "lookup_mci_licenses":
            return self._lookup_mci_licenses(**tool_input)
        if tool_name == "fetch_monshaat_requirements":
            return self._fetch_monshaat_requirements(**tool_input)
        if tool_name == "check_foreign_ownership_rules":
            return self._check_foreign_ownership_rules(**tool_input)
        if tool_name == "get_sector_regulator_requirements":
            return self._get_sector_regulator_requirements(**tool_input)
        raise NotImplementedError(f"Unknown tool: {tool_name}")

    def _lookup_mci_licenses(self, sector: str, ownership_type: str = "llc") -> dict:
        licenses = _MCI_LICENSES.get(sector.lower(), _MCI_LICENSES["default"])
        total_cost = sum(lic["cost_sar"] for lic in licenses)
        max_days = max(lic["timeline_days"] for lic in licenses)

        # Parallel processing possible — total is max of critical path, not sum
        return {
            "sector": sector,
            "ownership_type": ownership_type,
            "licenses": licenses,
            "total_cost_sar": total_cost,
            "critical_path_days": max_days,
            "sequential_days": sum(lic["timeline_days"] for lic in licenses),
        }

    def _fetch_monshaat_requirements(
        self, sector: str, investment_sar: float = 0
    ) -> dict:
        return {
            "monshaat_eligible": True,
            "registration_cost_sar": 0,
            "registration_days": 1,
            "benefits": [
                "Access to government procurement (منصة اعتماد)",
                "Monsha'at loans up to SAR 3M (قروض منشآت)",
                "Free business advisory services",
                "Saudization (نطاقات) compliance support",
                "Digital transformation grants up to SAR 250,000",
            ],
            "size_category": (
                "micro"
                if investment_sar < 500_000
                else "small"
                if investment_sar < 5_000_000
                else "medium"
            ),
            "url": "https://monshaat.gov.sa",
        }

    def _check_foreign_ownership_rules(
        self, sector: str, investor_nationality: str = "SA"
    ) -> dict:
        is_saudi = investor_nationality.upper() == "SA"
        restricted = {
            "real_estate": {
                "allowed": True,
                "min_capital_sar": 30_000_000,
                "misa_required": True,
            },
            "retail": {
                "allowed": True,
                "min_capital_sar": 26_000_000,
                "misa_required": True,
            },
            "media": {"allowed": False, "min_capital_sar": 0, "misa_required": True},
        }
        rule = restricted.get(
            sector.lower(),
            {
                "allowed": True,
                "min_capital_sar": 500_000,
                "misa_required": not is_saudi,
            },
        )

        return {
            "sector": sector,
            "investor_nationality": investor_nationality,
            "foreign_ownership_allowed": rule["allowed"],
            "requires_misa_licence": rule["misa_required"] and not is_saudi,
            "misa_licence_cost_sar": 10_000
            if (rule["misa_required"] and not is_saudi)
            else 0,
            "misa_licence_days": 30 if (rule["misa_required"] and not is_saudi) else 0,
            "min_capital_sar": rule["min_capital_sar"] if not is_saudi else 0,
            "negative_list": sector.lower() in ["media"],
        }

    def _get_sector_regulator_requirements(
        self, sector: str, city: str = "riyadh"
    ) -> dict:
        sector_regulators = {
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
        return sector_regulators.get(
            sector.lower(),
            {
                "regulator": "MCI",
                "regulator_ar": "وزارة التجارة",
                "license_name_en": "General Commercial License",
                "license_name_ar": "رخصة تجارية عامة",
                "cost_sar": 1_200,
                "timeline_days": 3,
                "annual_renewal_sar": 600,
                "requirements": ["Valid CR", "Municipality approval"],
            },
        )

    def _build_user_message(self, context: dict) -> str:
        sector = context.get("sector", "default")
        city = context.get("city", "Riyadh")
        nationality = context.get("investor_nationality", "SA")
        return (
            f"Identify all Saudi licenses and permits for this business.\n"
            f"Sector: {sector} | City: {city} | Investor: {nationality}\n\n"
            f"Steps:\n"
            f"1. Call lookup_mci_licenses for sector '{sector}'.\n"
            f"2. Call fetch_monshaat_requirements.\n"
            f"3. Call check_foreign_ownership_rules for nationality '{nationality}'.\n"
            f"4. Call get_sector_regulator_requirements for sector '{sector}'.\n\n"
            f"Return JSON: licenses, total_licensing_cost_sar, total_timeline_days, "
            f"compliance_flags, narrative_ar, narrative_en.\n\n"
            f"Full context:\n{json.dumps(context, ensure_ascii=False, indent=2)}"
        )
