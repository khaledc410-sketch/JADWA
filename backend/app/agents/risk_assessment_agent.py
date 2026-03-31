"""
RiskAssessmentAgent — comprehensive risk analysis across market, financial,
regulatory, and operational dimensions for Saudi businesses.
"""

import json
from typing import Any

from app.agents.base_agent import BaseAgent


# ---------------------------------------------------------------------------
# Saudi risk catalogue (mock — enriched from live regulatory feeds later)
# ---------------------------------------------------------------------------

_BASE_RISKS = [
    {
        "id": "R001",
        "category": "market",
        "description_en": "Oil price volatility affecting consumer spending and government budgets",
        "description_ar": "تقلبات أسعار النفط وتأثيرها على الإنفاق الاستهلاكي والميزانيات الحكومية",
        "likelihood": 3,
        "impact": 4,
        "mitigation_en": "Diversify revenue streams; target non-oil sectors; maintain 6-month cash reserve",
        "mitigation_ar": "تنويع مصادر الإيرادات؛ استهداف القطاعات غير النفطية؛ الاحتفاظ باحتياطي نقدي لستة أشهر",
    },
    {
        "id": "R002",
        "category": "regulatory",
        "description_en": "Regulatory changes — new Nitaqat quotas or sector-specific licensing updates",
        "description_ar": "التغييرات التنظيمية — حصص نطاقات الجديدة أو تحديثات ترخيص القطاع",
        "likelihood": 3,
        "impact": 3,
        "mitigation_en": "Monitor MHRSD and MCI circulars monthly; budget for compliance upgrades",
        "mitigation_ar": "متابعة منشورات وزارة الموارد البشرية ووزارة التجارة شهرياً؛ ميزانية لتحسينات الامتثال",
    },
    {
        "id": "R003",
        "category": "financial",
        "description_en": "Currency risk — SAR pegged to USD but exposure on USD-priced imports",
        "description_ar": "مخاطر العملة — الريال السعودي مرتبط بالدولار مع تعرض لواردات مسعرة بالدولار",
        "likelihood": 2,
        "impact": 3,
        "mitigation_en": "Negotiate SAR-denominated supply contracts; use forward contracts for large USD exposures",
        "mitigation_ar": "التفاوض على عقود توريد بالريال السعودي؛ استخدام عقود آجلة للتعرضات الكبيرة بالدولار",
    },
    {
        "id": "R004",
        "category": "operational",
        "description_en": "Talent shortage — qualified Saudi nationals in specialized roles",
        "description_ar": "شح المواهب — المواطنون السعوديون المؤهلون في الأدوار المتخصصة",
        "likelihood": 4,
        "impact": 3,
        "mitigation_en": "Partner with HRDF for training programs; offer competitive packages; invest in upskilling",
        "mitigation_ar": "الشراكة مع صندوق تنمية الموارد البشرية لبرامج التدريب؛ تقديم حزم تنافسية؛ الاستثمار في التطوير",
    },
    {
        "id": "R005",
        "category": "market",
        "description_en": "Intensifying competition — new regional and international entrants post-Vision 2030 opening",
        "description_ar": "تصاعد المنافسة — دخول منافسين إقليميين ودوليين جدد بعد انفتاح رؤية 2030",
        "likelihood": 4,
        "impact": 3,
        "mitigation_en": "Build brand loyalty early; differentiate on Saudization and local authenticity",
        "mitigation_ar": "بناء ولاء العلامة التجارية مبكراً؛ التمييز بالسعودة والأصالة المحلية",
    },
    {
        "id": "R006",
        "category": "financial",
        "description_en": "Interest rate risk — SAIBOR currently elevated (5.95%); impacts loan servicing",
        "description_ar": "مخاطر أسعار الفائدة — معدل السايبور مرتفع حالياً (5.95٪)؛ يؤثر على خدمة القروض",
        "likelihood": 3,
        "impact": 3,
        "mitigation_en": "Maximize SIDF concessional financing (3.5%); fix interest rate on long-term debt",
        "mitigation_ar": "تعظيم تمويل صندوق التنمية الصناعية الميسر (3.5٪)؛ تثبيت معدل الفائدة على الديون طويلة الأجل",
    },
    {
        "id": "R007",
        "category": "operational",
        "description_en": "Supply chain disruption — regional logistics and import dependency",
        "description_ar": "اضطراب سلسلة التوريد — الاعتماد على اللوجستيات الإقليمية والاستيراد",
        "likelihood": 3,
        "impact": 3,
        "mitigation_en": "Dual-source critical suppliers; maintain 8-week inventory buffer; favor local suppliers",
        "mitigation_ar": "مصادر ثنائية للموردين الحيويين؛ الحفاظ على احتياطي مخزون 8 أسابيع؛ تفضيل الموردين المحليين",
    },
    {
        "id": "R008",
        "category": "market",
        "description_en": "Consumer sentiment shifts — rapid change in Saudi consumer preferences (Gen-Z influence)",
        "description_ar": "تحولات معنويات المستهلك — التغير السريع في تفضيلات المستهلك السعودي (تأثير الجيل Z)",
        "likelihood": 3,
        "impact": 2,
        "mitigation_en": "Invest in brand community; conduct quarterly consumer pulse surveys; agile product iteration",
        "mitigation_ar": "الاستثمار في مجتمع العلامة التجارية؛ إجراء استطلاعات ربع سنوية؛ تكرار المنتج بمرونة",
    },
]

_SECTOR_SPECIFIC_RISKS = {
    "food_beverage": [
        {
            "id": "R101",
            "category": "regulatory",
            "description_en": "SFDA inspection failure — potential shutdown of food operations",
            "description_ar": "فشل تفتيش هيئة الغذاء والدواء — احتمالية إيقاف عمليات الأغذية",
            "likelihood": 2,
            "impact": 5,
            "mitigation_en": "Implement HACCP; conduct monthly internal audits; train all staff on food safety",
            "mitigation_ar": "تطبيق نظام الهاسب؛ إجراء مراجعات داخلية شهرية؛ تدريب الموظفين على سلامة الغذاء",
        },
    ],
    "real_estate": [
        {
            "id": "R201",
            "category": "market",
            "description_en": "Real estate market correction — oversupply in residential segment",
            "description_ar": "تصحيح سوق العقارات — فائض العرض في القطاع السكني",
            "likelihood": 3,
            "impact": 4,
            "mitigation_en": "Focus on affordable housing (aligned with Vision 2030 Sakani); phase development",
            "mitigation_ar": "التركيز على الإسكان الميسر (متوافق مع برنامج سكني في رؤية 2030)؛ التطوير المرحلي",
        },
    ],
    "technology": [
        {
            "id": "R301",
            "category": "operational",
            "description_en": "Cybersecurity breach — NCA compliance requirement (Essential Cybersecurity Controls)",
            "description_ar": "اختراق أمن المعلومات — متطلبات الامتثال للهيئة الوطنية للأمن السيبراني",
            "likelihood": 3,
            "impact": 5,
            "mitigation_en": "Implement NCA ECC framework; annual penetration testing; cyber insurance",
            "mitigation_ar": "تطبيق إطار عمل الضوابط الأساسية للأمن السيبراني؛ اختبار اختراق سنوي؛ تأمين إلكتروني",
        },
    ],
    "franchise": [
        {
            "id": "R401",
            "category": "operational",
            "description_en": "Franchisor relationship breakdown — unilateral contract termination",
            "description_ar": "انهيار العلاقة مع الجهة المانحة للامتياز — إنهاء العقد من جانب واحد",
            "likelihood": 2,
            "impact": 5,
            "mitigation_en": "Negotiate strong exit and renewal clauses; maintain performance above minimum thresholds",
            "mitigation_ar": "التفاوض على بنود خروج وتجديد قوية؛ الحفاظ على الأداء فوق الحد الأدنى",
        },
    ],
}


def _compute_score(likelihood: int, impact: int) -> int:
    return likelihood * impact


class RiskAssessmentAgent(BaseAgent):
    name: str = "RiskAssessmentAgent"
    description: str = (
        "Saudi business risk analysis: market, financial, regulatory, operational"
    )
    temperature: float = 0.3

    @property
    def system_prompt(self) -> str:
        return (
            "أنت محلل مخاطر متخصص في بيئة الأعمال السعودية.\n\n"
            "You are a risk analyst specializing in the Saudi business environment. You:\n"
            "- Score risks by likelihood (1-5) and impact (1-5)\n"
            "- Categorize: market, financial, regulatory, operational\n"
            "- Propose practical, Saudi-context mitigations\n"
            "- Use Saudi-specific risk factors: oil price dependency, regulatory pace, "
            "  Saudization compliance, competition from Vision 2030 new entrants\n"
            "- Generate a SWOT analysis\n\n"
            "Instructions:\n"
            "- Risk score = likelihood × impact (max 25)\n"
            "- Overall rating: low (<8), medium (8-15), high (16-20), critical (>20)\n"
            "- Provide Arabic and English for all risk descriptions and mitigations.\n"
            "Return a JSON object matching the output schema exactly."
        )

    @property
    def tools(self) -> list:
        return [
            {
                "name": "assess_market_risks",
                "description": "Assesses market-specific risks for a Saudi sector and city.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sector": {"type": "string"},
                        "city": {"type": "string"},
                        "investment_sar": {"type": "number"},
                    },
                    "required": ["sector"],
                },
            },
            {
                "name": "assess_financial_risks",
                "description": "Assesses financial risks including interest rate, currency, and liquidity.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "investment_sar": {"type": "number"},
                        "debt_equity_ratio": {"type": "number"},
                        "sector": {"type": "string"},
                    },
                    "required": ["investment_sar"],
                },
            },
            {
                "name": "assess_regulatory_risks",
                "description": "Assesses regulatory and compliance risks for a Saudi sector.",
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
                "name": "generate_risk_matrix",
                "description": (
                    "Compiles all risks into a risk matrix and generates SWOT analysis "
                    "for the business."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sector": {"type": "string"},
                        "risks": {"type": "array", "items": {"type": "object"}},
                    },
                    "required": ["sector"],
                },
            },
        ]

    # ------------------------------------------------------------------
    # Tool implementations
    # ------------------------------------------------------------------

    def execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        if tool_name == "assess_market_risks":
            return self._assess_market_risks(**tool_input)
        if tool_name == "assess_financial_risks":
            return self._assess_financial_risks(**tool_input)
        if tool_name == "assess_regulatory_risks":
            return self._assess_regulatory_risks(**tool_input)
        if tool_name == "generate_risk_matrix":
            return self._generate_risk_matrix(**tool_input)
        raise NotImplementedError(f"Unknown tool: {tool_name}")

    def _assess_market_risks(
        self, sector: str, city: str = "riyadh", investment_sar: float = 1_000_000
    ) -> list:
        market_risks = [r for r in _BASE_RISKS if r["category"] == "market"]
        sector_risks = [
            r
            for r in _SECTOR_SPECIFIC_RISKS.get(sector.lower(), [])
            if r["category"] == "market"
        ]
        all_risks = market_risks + sector_risks
        for r in all_risks:
            r["score"] = _compute_score(r["likelihood"], r["impact"])
        return all_risks

    def _assess_financial_risks(
        self,
        investment_sar: float,
        debt_equity_ratio: float = 0.6,
        sector: str = "default",
    ) -> list:
        financial_risks = [r for r in _BASE_RISKS if r["category"] == "financial"]
        # Adjust likelihood based on debt ratio
        for r in financial_risks:
            if debt_equity_ratio > 0.7 and r["id"] == "R006":
                r["likelihood"] = min(5, r["likelihood"] + 1)
            r["score"] = _compute_score(r["likelihood"], r["impact"])
        return financial_risks

    def _assess_regulatory_risks(
        self, sector: str, investor_nationality: str = "SA"
    ) -> list:
        reg_risks = [r for r in _BASE_RISKS if r["category"] == "regulatory"]
        sector_risks = [
            r
            for r in _SECTOR_SPECIFIC_RISKS.get(sector.lower(), [])
            if r["category"] == "regulatory"
        ]
        all_risks = reg_risks + sector_risks

        # Foreign investors have higher regulatory risk
        if investor_nationality.upper() != "SA":
            for r in all_risks:
                r["likelihood"] = min(5, r["likelihood"] + 1)

        for r in all_risks:
            r["score"] = _compute_score(r["likelihood"], r["impact"])
        return all_risks

    def _generate_risk_matrix(self, sector: str, risks: list = None) -> dict:
        if risks is None:
            all_risks = list(_BASE_RISKS)
            sector_specific = _SECTOR_SPECIFIC_RISKS.get(sector.lower(), [])
            all_risks.extend(sector_specific)
        else:
            all_risks = risks

        for r in all_risks:
            r["score"] = _compute_score(r.get("likelihood", 3), r.get("impact", 3))

        avg_score = (
            sum(r["score"] for r in all_risks) / len(all_risks) if all_risks else 0
        )
        if avg_score < 8:
            overall = "low"
        elif avg_score < 15:
            overall = "medium"
        elif avg_score < 20:
            overall = "high"
        else:
            overall = "critical"

        # SWOT
        swot = {
            "strengths": [
                "Saudi-owned business benefits from national preference policies",
                "Vision 2030 government tailwinds for most sectors",
                "Young, growing Saudi consumer base (median age 29)",
                "Strong government support programs (HRDF, SIDF, Monsha'at)",
            ],
            "weaknesses": [
                "Saudization compliance adds to labor cost structure",
                "Dependence on imported goods (exposure to global supply chains)",
                "SME financing access can be challenging for first-time entrepreneurs",
            ],
            "opportunities": [
                "Vision 2030 domestic tourism target: 150M visitors by 2030",
                "Growing female workforce participation (33%+, exceeding 2030 target)",
                "Digital payment adoption: 68% cashless (target 80% by 2030)",
                f"Sector-specific Vision 2030 investment in {sector}",
            ],
            "threats": [
                "Geopolitical instability in the broader MENA region",
                "Rapid competitive entry from international brands post-liberalization",
                "Technology disruption risk (AI, automation)",
                "Potential changes to VAT or Zakat regulations",
            ],
        }

        return {
            "all_risks": all_risks,
            "overall_risk_score": overall,
            "average_risk_score": round(avg_score, 1),
            "high_priority_risks": [r for r in all_risks if r["score"] >= 12],
            "swot": swot,
        }

    def _build_user_message(self, context: dict) -> str:
        sector = context.get("sector", "default")
        investment = context.get("investment_amount_sar", 1_000_000)
        nationality = context.get("investor_nationality", "SA")
        return (
            f"Conduct a comprehensive risk assessment for this Saudi business.\n"
            f"Sector: {sector} | Investment: SAR {investment:,.0f} | Investor: {nationality}\n\n"
            f"Steps:\n"
            f"1. Call assess_market_risks for sector '{sector}'.\n"
            f"2. Call assess_financial_risks with investment SAR {investment:,.0f}.\n"
            f"3. Call assess_regulatory_risks for '{sector}' with nationality '{nationality}'.\n"
            f"4. Call generate_risk_matrix to compile all risks and generate SWOT.\n\n"
            f"Return JSON: risks (array), overall_risk_score, swot, narrative_ar, narrative_en.\n\n"
            f"Full context:\n{json.dumps(context, ensure_ascii=False, indent=2)}"
        )
