"""
Vision2030Agent — evaluates alignment with Vision 2030 pillars and identifies
applicable government incentive programs, SEZ benefits, and MISA packages.
"""

import json
from typing import Any

from app.agents.base_agent import BaseAgent


# ---------------------------------------------------------------------------
# Vision 2030 programs database (mock — live Monsha'at / MISA API later)
# ---------------------------------------------------------------------------

_VISION_PILLARS = {
    "economic_diversification": {
        "name_ar": "التنويع الاقتصادي",
        "name_en": "Economic Diversification",
        "sectors": ["manufacturing", "technology", "logistics", "mining", "tourism"],
        "kpi": "Non-oil GDP target: 50% of GDP by 2030 (currently 45%)",
    },
    "sme_empowerment": {
        "name_ar": "تمكين المنشآت الصغيرة والمتوسطة",
        "name_en": "SME Empowerment",
        "sectors": ["all"],
        "kpi": "SME contribution to GDP target: 35% by 2030 (currently 28%)",
    },
    "national_transformation": {
        "name_ar": "برنامج التحول الوطني",
        "name_en": "National Transformation Program",
        "sectors": ["technology", "healthcare", "education", "logistics"],
        "kpi": "Digital economy contribution: 19.2% of GDP by 2030",
    },
    "quality_of_life": {
        "name_ar": "برنامج جودة الحياة",
        "name_en": "Quality of Life Program",
        "sectors": [
            "hospitality",
            "food_beverage",
            "entertainment",
            "sports",
            "education",
        ],
        "kpi": "Resident happiness index target: 7.4/10 by 2030",
    },
    "housing_development": {
        "name_ar": "برنامج الإسكان",
        "name_en": "Housing Development Program",
        "sectors": ["real_estate", "construction"],
        "kpi": "Saudi homeownership target: 70% by 2030 (currently 62%)",
    },
    "financial_sector": {
        "name_ar": "برنامج تطوير القطاع المالي",
        "name_en": "Financial Sector Development",
        "sectors": ["finance", "fintech", "insurance"],
        "kpi": "Cashless transactions target: 80% by 2030 (currently 68%)",
    },
    "human_capital": {
        "name_ar": "تنمية الموارد البشرية",
        "name_en": "Human Capital Development",
        "sectors": ["education", "training", "healthcare"],
        "kpi": "Female labor participation target: 30% (currently 33% — exceeded)",
    },
}

_INCENTIVE_PROGRAMS = {
    "all": [
        {
            "name_ar": "برنامج منشآت للتمويل",
            "name_en": "Monsha'at SME Financing Program",
            "provider": "Monsha'at",
            "benefit_sar": 3_000_000,
            "benefit_description_en": "Concessional loans up to SAR 3M at 0% interest for qualifying SMEs",
            "eligibility_en": "Saudi-owned SME with CR, minimum 1 year operational",
            "url": "https://monshaat.gov.sa",
        },
        {
            "name_ar": "صندوق صغار المنتجين",
            "name_en": "Small Producers Fund",
            "provider": "SIDF",
            "benefit_sar": 5_000_000,
            "benefit_description_en": "SIDF concessional loans at 3.5% for manufacturing and industrial projects",
            "eligibility_en": "Manufacturing sector SMEs with MODON zone preference",
            "url": "https://sidf.gov.sa",
        },
        {
            "name_ar": "برنامج نطاقات المميزة",
            "name_en": "Nitaqat Platinum Rewards",
            "provider": "MHRSD",
            "benefit_sar": 50_000,
            "benefit_description_en": "Fee waivers, priority government procurement access for Platinum Nitaqat companies",
            "eligibility_en": "Companies achieving Platinum Saudization band",
            "url": "https://hrsd.gov.sa",
        },
    ],
    "technology": [
        {
            "name_ar": "برنامج نيوم للشركات التقنية",
            "name_en": "NEOM Tech Startup Program",
            "provider": "NEOM",
            "benefit_sar": 2_000_000,
            "benefit_description_en": "Up to SAR 2M equity-free grants for tech startups aligned with NEOM sectors",
            "eligibility_en": "Tech startups in AI, robotics, clean energy, biotech",
            "url": "https://neom.com/startups",
        },
        {
            "name_ar": "صندوق ريادة الأعمال التقنية",
            "name_en": "STC Ventures Tech Fund",
            "provider": "STC Ventures",
            "benefit_sar": 10_000_000,
            "benefit_description_en": "Equity investment SAR 2-10M for Series A Saudi tech startups",
            "eligibility_en": "Tech startups with >SAR 2M ARR or strong traction",
            "url": "https://stcventures.com",
        },
        {
            "name_ar": "منحة التحول الرقمي للمنشآت",
            "name_en": "Monsha'at Digital Transformation Grant",
            "provider": "Monsha'at",
            "benefit_sar": 250_000,
            "benefit_description_en": "SAR 250K grant for digitizing SME operations (ERP, cloud, cybersecurity)",
            "eligibility_en": "Saudi SMEs with valid CR in any sector",
            "url": "https://monshaat.gov.sa/digital",
        },
    ],
    "manufacturing": [
        {
            "name_ar": "برنامج المحتوى المحلي",
            "name_en": "Saudi Content Program (IKTVA equivalent)",
            "provider": "Ministry of Industry",
            "benefit_sar": 15_000_000,
            "benefit_description_en": "Preferential procurement from Saudi manufacturers for government contracts",
            "eligibility_en": "Manufacturers with >30% Saudi content",
            "url": "https://industry.gov.sa",
        },
        {
            "name_ar": "مجمعات مدن تقنية (مدن)",
            "name_en": "MODON Industrial Zones",
            "provider": "MODON",
            "benefit_sar": 2_000_000,
            "benefit_description_en": "Subsidized land, utilities, and infrastructure in industrial cities",
            "eligibility_en": "Manufacturing companies with approved industrial project",
            "url": "https://modon.gov.sa",
        },
    ],
    "real_estate": [
        {
            "name_ar": "برنامج مسكن",
            "name_en": "Sakani Affordable Housing Program",
            "provider": "MOH/Real Estate Development Fund",
            "benefit_sar": 500_000,
            "benefit_description_en": "Up to SAR 500K subsidy for affordable housing developers under Sakani",
            "eligibility_en": "Developers building units below SAR 750,000 in designated areas",
            "url": "https://sakani.housing.gov.sa",
        },
    ],
    "tourism": [
        {
            "name_ar": "صندوق تطوير السياحة",
            "name_en": "Tourism Development Fund",
            "provider": "TDF",
            "benefit_sar": 50_000_000,
            "benefit_description_en": "Financing up to SAR 50M at preferential rates for tourism projects",
            "eligibility_en": "Tourism and hospitality projects with >50 rooms or SAR 5M+ investment",
            "url": "https://tdf.gov.sa",
        },
    ],
}

_SEZ_BENEFITS = {
    "king_abdullah_economic_city": {
        "name_ar": "مدينة الملك عبدالله الاقتصادية",
        "name_en": "King Abdullah Economic City (KAEC)",
        "location": "Jeddah - Rabigh",
        "tax_exemption_years": 20,
        "customs_benefits": "0% customs on goods within the zone",
        "sectors": ["manufacturing", "logistics", "technology"],
    },
    "jazan_sez": {
        "name_ar": "منطقة جازان الاقتصادية الخاصة",
        "name_en": "Jazan Special Economic Zone",
        "location": "Jazan",
        "tax_exemption_years": 20,
        "customs_benefits": "Reduced customs and streamlined procedures",
        "sectors": ["manufacturing", "energy", "chemicals"],
    },
    "cloud_computing_zone": {
        "name_ar": "منطقة الحوسبة السحابية",
        "name_en": "Cloud Computing Zone (CCZ) — Riyadh",
        "location": "Riyadh",
        "tax_exemption_years": 10,
        "customs_benefits": "0% customs on tech equipment",
        "sectors": ["technology"],
    },
}


class Vision2030Agent(BaseAgent):
    name: str = "Vision2030Agent"
    description: str = "Vision 2030 alignment scoring and government incentive mapping"
    temperature: float = 0.3

    @property
    def system_prompt(self) -> str:
        return (
            "أنت متخصص في رؤية المملكة العربية السعودية 2030، لديك معرفة عميقة بأهداف الرؤية، "
            "وحوافز الاستثمار من هيئة الاستثمار (مساء)، والمناطق الاقتصادية الخاصة، "
            "وبرامج دعم رواد الأعمال.\n\n"
            "You are a Vision 2030 specialist with deep knowledge of:\n"
            "- Vision 2030 pillars and National Transformation Program (NTP) targets\n"
            "- MISA (Ministry of Investment) incentives and packages\n"
            "- Special Economic Zones (SEZs) benefits by sector\n"
            "- Monsha'at, HRDF, SIDF, and other government support programs\n"
            "- Sector-specific Vision 2030 KPIs and targets\n\n"
            "Instructions:\n"
            "- Score Vision alignment (0-100) based on sector and project characteristics.\n"
            "- Identify all applicable incentive programs.\n"
            "- Recommend SEZ consideration if applicable.\n"
            "- Provide Arabic and English narratives.\n"
            "Return a JSON object matching the output schema exactly."
        )

    @property
    def tools(self) -> list:
        return [
            {
                "name": "evaluate_vision_alignment",
                "description": (
                    "Evaluates the business project's alignment with Vision 2030 pillars "
                    "and National Transformation Program targets."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sector": {"type": "string"},
                        "is_saudi_owned": {"type": "boolean"},
                        "creates_jobs": {"type": "boolean"},
                        "uses_technology": {"type": "boolean"},
                        "exports_potential": {"type": "boolean"},
                    },
                    "required": ["sector"],
                },
            },
            {
                "name": "lookup_incentive_programs",
                "description": (
                    "Returns all government incentive programs applicable to a sector, "
                    "including grants, loans, subsidies, and fee waivers."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sector": {"type": "string"},
                        "investment_sar": {"type": "number"},
                        "is_saudi_owned": {"type": "boolean"},
                    },
                    "required": ["sector"],
                },
            },
            {
                "name": "calculate_alignment_score",
                "description": (
                    "Calculates a quantitative Vision 2030 alignment score (0-100) "
                    "based on sector, ownership, job creation, technology use, and other factors."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sector": {"type": "string"},
                        "pillar_scores": {"type": "object"},
                    },
                    "required": ["sector"],
                },
            },
            {
                "name": "fetch_sez_benefits",
                "description": (
                    "Returns benefits of applicable Special Economic Zones (SEZs) "
                    "for a given sector and location."
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
        if tool_name == "evaluate_vision_alignment":
            return self._evaluate_vision_alignment(**tool_input)
        if tool_name == "lookup_incentive_programs":
            return self._lookup_incentive_programs(**tool_input)
        if tool_name == "calculate_alignment_score":
            return self._calculate_alignment_score(**tool_input)
        if tool_name == "fetch_sez_benefits":
            return self._fetch_sez_benefits(**tool_input)
        raise NotImplementedError(f"Unknown tool: {tool_name}")

    def _evaluate_vision_alignment(
        self,
        sector: str,
        is_saudi_owned: bool = True,
        creates_jobs: bool = True,
        uses_technology: bool = False,
        exports_potential: bool = False,
    ) -> dict:
        aligned_pillars = []

        for pillar_key, pillar in _VISION_PILLARS.items():
            if "all" in pillar["sectors"] or sector.lower() in pillar["sectors"]:
                aligned_pillars.append(
                    {
                        "pillar_key": pillar_key,
                        "name_ar": pillar["name_ar"],
                        "name_en": pillar["name_en"],
                        "kpi": pillar["kpi"],
                    }
                )

        # Always add SME empowerment
        if not any(p["pillar_key"] == "sme_empowerment" for p in aligned_pillars):
            aligned_pillars.append(
                {
                    "pillar_key": "sme_empowerment",
                    "name_ar": _VISION_PILLARS["sme_empowerment"]["name_ar"],
                    "name_en": _VISION_PILLARS["sme_empowerment"]["name_en"],
                    "kpi": _VISION_PILLARS["sme_empowerment"]["kpi"],
                }
            )

        return {
            "sector": sector,
            "aligned_pillars": [p["pillar_key"] for p in aligned_pillars],
            "pillar_details": aligned_pillars,
            "alignment_factors": {
                "saudi_ownership": is_saudi_owned,
                "job_creation": creates_jobs,
                "technology_adoption": uses_technology,
                "export_potential": exports_potential,
            },
        }

    def _lookup_incentive_programs(
        self,
        sector: str,
        investment_sar: float = 1_000_000,
        is_saudi_owned: bool = True,
    ) -> dict:
        programs = list(_INCENTIVE_PROGRAMS.get("all", []))
        sector_programs = _INCENTIVE_PROGRAMS.get(sector.lower(), [])
        programs.extend(sector_programs)

        total_potential_benefit = sum(p.get("benefit_sar", 0) for p in programs)

        return {
            "sector": sector,
            "programs": programs,
            "total_programs": len(programs),
            "total_potential_benefit_sar": total_potential_benefit,
            "note_ar": "المبالغ تقديرية وتخضع لشروط الأهلية",
            "note_en": "Amounts are indicative and subject to eligibility criteria",
        }

    def _calculate_alignment_score(
        self, sector: str, pillar_scores: dict = None
    ) -> dict:
        sector_base_scores = {
            "technology": 88,
            "manufacturing": 82,
            "logistics": 80,
            "real_estate": 75,
            "healthcare": 78,
            "education": 76,
            "food_beverage": 72,
            "franchise": 70,
            "retail": 68,
            "hospitality": 74,
            "energy": 85,
            "default": 65,
        }
        base = sector_base_scores.get(sector.lower(), 65)

        if pillar_scores:
            adjustment = sum(pillar_scores.values()) / len(pillar_scores) - 50
            base = min(100, base + adjustment / 10)

        return {
            "alignment_score": round(base),
            "sector": sector,
            "score_breakdown": {
                "economic_diversification": min(100, base + 5),
                "sme_empowerment": min(100, base + 3),
                "job_creation": min(100, base + 4),
                "technology_adoption": min(
                    100, base - 5 if sector != "technology" else base + 5
                ),
            },
            "benchmark": "Saudi national average SME alignment score: 72",
        }

    def _fetch_sez_benefits(self, sector: str, city: str = "riyadh") -> list:
        applicable = []
        for sez_key, sez in _SEZ_BENEFITS.items():
            if sector.lower() in sez["sectors"]:
                applicable.append(
                    {
                        "sez_id": sez_key,
                        "name_ar": sez["name_ar"],
                        "name_en": sez["name_en"],
                        "location": sez["location"],
                        "tax_exemption_years": sez["tax_exemption_years"],
                        "customs_benefits": sez["customs_benefits"],
                    }
                )
        return (
            applicable
            if applicable
            else [
                {
                    "note": "No SEZ specifically targets this sector — standard MISA incentives apply."
                }
            ]
        )

    def _build_user_message(self, context: dict) -> str:
        sector = context.get("sector", "default")
        is_saudi = context.get("investor_nationality", "SA") == "SA"
        investment = context.get("investment_amount_sar", 1_000_000)
        return (
            f"Evaluate Vision 2030 alignment and incentives for this Saudi business.\n"
            f"Sector: {sector} | Saudi-owned: {is_saudi} | Investment: SAR {investment:,.0f}\n\n"
            f"Steps:\n"
            f"1. Call evaluate_vision_alignment for sector '{sector}'.\n"
            f"2. Call calculate_alignment_score.\n"
            f"3. Call lookup_incentive_programs for '{sector}'.\n"
            f"4. Call fetch_sez_benefits to check for Special Economic Zone applicability.\n\n"
            f"Return JSON: alignment_score, aligned_pillars, applicable_programs, "
            f"narrative_ar, narrative_en.\n\n"
            f"Full context:\n{json.dumps(context, ensure_ascii=False, indent=2)}"
        )
