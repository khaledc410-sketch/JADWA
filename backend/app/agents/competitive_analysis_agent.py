"""
CompetitiveAnalysisAgent — competitive landscape mapping, positioning analysis,
and differentiation strategy recommendations for the Saudi market.
"""

import json
from typing import Any

from app.agents.base_agent import BaseAgent


# ---------------------------------------------------------------------------
# Saudi competitor database (mock — web scraping / Marqeta data later)
# ---------------------------------------------------------------------------

_SECTOR_COMPETITORS = {
    "food_beverage": [
        {
            "name": "Herfy",
            "type": "direct",
            "market_share_percent": 12,
            "price_positioning": "value",
            "strengths": ["strong Saudi brand", "wide coverage"],
            "weaknesses": ["aging brand image"],
        },
        {
            "name": "Al Baik",
            "type": "direct",
            "market_share_percent": 18,
            "price_positioning": "value",
            "strengths": ["cult following", "low price", "Halal trusted"],
            "weaknesses": ["limited menu", "no delivery"],
        },
        {
            "name": "McDonald's",
            "type": "direct",
            "market_share_percent": 15,
            "price_positioning": "mid",
            "strengths": ["global brand", "digital ordering"],
            "weaknesses": ["health perception", "high royalty"],
        },
        {
            "name": "Hungerstation",
            "type": "indirect",
            "market_share_percent": 8,
            "price_positioning": "premium",
            "strengths": ["delivery aggregator", "large selection"],
            "weaknesses": ["high commission fees"],
        },
    ],
    "retail": [
        {
            "name": "Panda",
            "type": "direct",
            "market_share_percent": 22,
            "price_positioning": "mid",
            "strengths": ["established network", "Saudi trust"],
            "weaknesses": ["slow digital transformation"],
        },
        {
            "name": "Carrefour KSA",
            "type": "direct",
            "market_share_percent": 18,
            "price_positioning": "value",
            "strengths": ["international brand", "wide SKUs"],
            "weaknesses": ["foreign brand perception"],
        },
        {
            "name": "Nana",
            "type": "indirect",
            "market_share_percent": 5,
            "price_positioning": "premium",
            "strengths": ["instant delivery", "tech-savvy"],
            "weaknesses": ["limited geographic coverage"],
        },
        {
            "name": "BinDawood",
            "type": "direct",
            "market_share_percent": 14,
            "price_positioning": "mid",
            "strengths": ["strong regional brand", "loyalty program"],
            "weaknesses": ["limited online presence"],
        },
    ],
    "technology": [
        {
            "name": "STC",
            "type": "indirect",
            "market_share_percent": 35,
            "price_positioning": "premium",
            "strengths": ["government backing", "infrastructure"],
            "weaknesses": ["slow innovation"],
        },
        {
            "name": "Elm",
            "type": "direct",
            "market_share_percent": 20,
            "price_positioning": "premium",
            "strengths": ["government contracts", "trust"],
            "weaknesses": ["non-competitive for SMEs"],
        },
        {
            "name": "Tawuniya",
            "type": "indirect",
            "market_share_percent": 10,
            "price_positioning": "mid",
            "strengths": ["established brand", "insurance tech"],
            "weaknesses": ["narrow vertical focus"],
        },
        {
            "name": "Local Startups",
            "type": "direct",
            "market_share_percent": 5,
            "price_positioning": "value",
            "strengths": ["agile", "niche focus"],
            "weaknesses": ["limited funding", "short track record"],
        },
    ],
    "healthcare": [
        {
            "name": "Saudi German Hospital",
            "type": "direct",
            "market_share_percent": 8,
            "price_positioning": "premium",
            "strengths": ["brand trust", "wide specialties"],
            "weaknesses": ["high cost"],
        },
        {
            "name": "Mouwasat",
            "type": "direct",
            "market_share_percent": 6,
            "price_positioning": "premium",
            "strengths": ["quality care", "Eastern Province presence"],
            "weaknesses": ["limited Riyadh locations"],
        },
        {
            "name": "Tadawi",
            "type": "direct",
            "market_share_percent": 4,
            "price_positioning": "mid",
            "strengths": ["accessible pricing", "wide network"],
            "weaknesses": ["brand recognition"],
        },
    ],
    "real_estate": [
        {
            "name": "Emaar KSA",
            "type": "direct",
            "market_share_percent": 12,
            "price_positioning": "premium",
            "strengths": ["brand", "master-planned communities"],
            "weaknesses": ["high price point"],
        },
        {
            "name": "Dar Al Arkan",
            "type": "direct",
            "market_share_percent": 10,
            "price_positioning": "premium",
            "strengths": ["Saudi brand", "government projects"],
            "weaknesses": ["execution delays"],
        },
        {
            "name": "Akaria",
            "type": "direct",
            "market_share_percent": 8,
            "price_positioning": "mid",
            "strengths": ["Riyadh focus", "affordable"],
            "weaknesses": ["limited product range"],
        },
    ],
    "franchise": [
        {
            "name": "Subway KSA",
            "type": "direct",
            "market_share_percent": 10,
            "price_positioning": "value",
            "strengths": ["low investment", "known brand"],
            "weaknesses": ["margin pressure"],
        },
        {
            "name": "Baskin Robbins",
            "type": "direct",
            "market_share_percent": 8,
            "price_positioning": "mid",
            "strengths": ["dessert niche", "mall presence"],
            "weaknesses": ["seasonal demand"],
        },
    ],
    "default": [
        {
            "name": "Market Leader A",
            "type": "direct",
            "market_share_percent": 20,
            "price_positioning": "mid",
            "strengths": ["established brand", "distribution"],
            "weaknesses": ["slow to innovate"],
        },
        {
            "name": "Market Leader B",
            "type": "direct",
            "market_share_percent": 15,
            "price_positioning": "premium",
            "strengths": ["premium quality", "loyalty base"],
            "weaknesses": ["high price point"],
        },
        {
            "name": "Low-cost Player",
            "type": "direct",
            "market_share_percent": 10,
            "price_positioning": "value",
            "strengths": ["price", "accessibility"],
            "weaknesses": ["quality perception"],
        },
    ],
}


class CompetitiveAnalysisAgent(BaseAgent):
    name: str = "CompetitiveAnalysisAgent"
    description: str = "Saudi competitive landscape, positioning, and differentiation"
    temperature: float = 0.4

    @property
    def system_prompt(self) -> str:
        return (
            "أنت محلل استخباراتي تنافسي متخصص في السوق السعودي، تحدد المنافسين المباشرين وغير المباشرين، "
            "وتحلل تموضعهم، وتوصي باستراتيجيات التمييز.\n\n"
            "You are a competitive intelligence analyst specializing in the Saudi market. You:\n"
            "- Identify direct and indirect competitors in the sector\n"
            "- Analyze pricing, positioning, and market share\n"
            "- Generate a positioning matrix (price vs. quality axes)\n"
            "- Recommend differentiation strategies specific to the Saudi market\n"
            "- Assess competitive intensity (low/medium/high/very_high)\n\n"
            "Instructions:\n"
            "- Focus on Saudi-specific players and dynamics.\n"
            "- Consider Vision 2030 new entrants and disruptions.\n"
            "- Provide SWOT for the new entrant vs. incumbents.\n"
            "- Use both Arabic and English in narratives.\n"
            "Return a JSON object matching the output schema exactly."
        )

    @property
    def tools(self) -> list:
        return [
            {
                "name": "map_local_competitors",
                "description": (
                    "Maps direct and indirect competitors in a Saudi sector and city, "
                    "returning market share estimates and key characteristics."
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
            {
                "name": "analyze_competitor_pricing",
                "description": (
                    "Analyzes pricing strategies of key competitors in the Saudi market, "
                    "returning price ranges and positioning tiers."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sector": {"type": "string"},
                        "target_segment": {"type": "string"},
                    },
                    "required": ["sector"],
                },
            },
            {
                "name": "generate_positioning_matrix",
                "description": (
                    "Generates a 2x2 positioning matrix (price vs. quality) "
                    "placing competitors and identifying white space opportunities."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sector": {"type": "string"},
                        "competitors": {
                            "type": "array",
                            "items": {"type": "object"},
                        },
                    },
                    "required": ["sector"],
                },
            },
            {
                "name": "suggest_differentiation",
                "description": (
                    "Suggests specific differentiation strategies for a new entrant "
                    "in the Saudi market based on competitive gaps and consumer trends."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sector": {"type": "string"},
                        "competitive_intensity": {"type": "string"},
                        "target_segment": {"type": "string"},
                    },
                    "required": ["sector"],
                },
            },
        ]

    # ------------------------------------------------------------------
    # Tool implementations
    # ------------------------------------------------------------------

    def execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        if tool_name == "map_local_competitors":
            return self._map_local_competitors(**tool_input)
        if tool_name == "analyze_competitor_pricing":
            return self._analyze_competitor_pricing(**tool_input)
        if tool_name == "generate_positioning_matrix":
            return self._generate_positioning_matrix(**tool_input)
        if tool_name == "suggest_differentiation":
            return self._suggest_differentiation(**tool_input)
        raise NotImplementedError(f"Unknown tool: {tool_name}")

    def _map_local_competitors(self, sector: str, city: str = "riyadh") -> dict:
        competitors = _SECTOR_COMPETITORS.get(
            sector.lower(), _SECTOR_COMPETITORS["default"]
        )
        total_mapped_share = sum(c["market_share_percent"] for c in competitors)
        direct = [c for c in competitors if c["type"] == "direct"]
        indirect = [c for c in competitors if c["type"] == "indirect"]

        intensity_map = {0: "low", 1: "low", 2: "medium", 3: "high", 4: "very_high"}
        intensity = intensity_map.get(min(len(direct), 4), "very_high")

        return {
            "sector": sector,
            "city": city,
            "competitors": competitors,
            "direct_count": len(direct),
            "indirect_count": len(indirect),
            "total_mapped_share_percent": total_mapped_share,
            "fragmented_market_remaining_pct": max(0, 100 - total_mapped_share),
            "competitive_intensity": intensity,
        }

    def _analyze_competitor_pricing(
        self, sector: str, target_segment: str = "mid_market"
    ) -> dict:
        pricing_data = {
            "food_beverage": {
                "value_range_sar": {
                    "avg_ticket": 25,
                    "monthly_revenue_potential": 80_000,
                },
                "mid_range_sar": {
                    "avg_ticket": 55,
                    "monthly_revenue_potential": 150_000,
                },
                "premium_range_sar": {
                    "avg_ticket": 120,
                    "monthly_revenue_potential": 200_000,
                },
            },
            "retail": {
                "value_range_sar": {
                    "avg_basket": 120,
                    "monthly_revenue_potential": 200_000,
                },
                "mid_range_sar": {
                    "avg_basket": 280,
                    "monthly_revenue_potential": 450_000,
                },
                "premium_range_sar": {
                    "avg_basket": 600,
                    "monthly_revenue_potential": 600_000,
                },
            },
            "default": {
                "value_range_sar": {
                    "avg_order": 150,
                    "monthly_revenue_potential": 100_000,
                },
                "mid_range_sar": {
                    "avg_order": 350,
                    "monthly_revenue_potential": 250_000,
                },
                "premium_range_sar": {
                    "avg_order": 800,
                    "monthly_revenue_potential": 400_000,
                },
            },
        }
        data = pricing_data.get(sector.lower(), pricing_data["default"])
        return {
            "sector": sector,
            "pricing_tiers": data,
            "recommended_entry_tier": "mid_range_sar",
            "price_sensitivity": "high"
            if sector in ["food_beverage", "retail"]
            else "medium",
        }

    def _generate_positioning_matrix(
        self, sector: str, competitors: list = None
    ) -> dict:
        if competitors is None:
            competitors = _SECTOR_COMPETITORS.get(
                sector.lower(), _SECTOR_COMPETITORS["default"]
            )

        quadrants = {
            "premium_high_quality": [],
            "premium_low_quality": [],
            "value_high_quality": [],
            "value_low_quality": [],
        }
        for c in competitors:
            pos = c.get("price_positioning", "mid")
            quality_score = len(c.get("strengths", [])) - len(c.get("weaknesses", []))
            if pos == "premium":
                quadrants[
                    "premium_high_quality"
                    if quality_score >= 0
                    else "premium_low_quality"
                ].append(c["name"])
            else:
                quadrants[
                    "value_high_quality" if quality_score >= 0 else "value_low_quality"
                ].append(c["name"])

        return {
            "matrix": quadrants,
            "white_space": "value_high_quality"
            if not quadrants["value_high_quality"]
            else "premium_high_quality",
            "recommended_position": "mid_market_quality_focus",
            "rationale_en": "Position at mid-market price with clear quality differentiation to capture price-sensitive yet quality-conscious Saudi consumers.",
            "rationale_ar": "التموضع في منتصف السوق مع تمييز واضح بالجودة لاستهداف المستهلكين السعوديين الواعين بالسعر والجودة.",
        }

    def _suggest_differentiation(
        self,
        sector: str,
        competitive_intensity: str = "high",
        target_segment: str = "young_professionals",
    ) -> dict:
        strategies = {
            "food_beverage": [
                {
                    "strategy_en": "Digital-first ordering with gamification",
                    "strategy_ar": "طلب رقمي أولاً مع عناصر الألعاب",
                    "impact": "high",
                },
                {
                    "strategy_en": "Hyper-local Saudi flavors fusion",
                    "strategy_ar": "دمج النكهات السعودية المحلية",
                    "impact": "high",
                },
                {
                    "strategy_en": "Subscription meal plans (Vision 2030 wellness)",
                    "strategy_ar": "خطط وجبات اشتراكية",
                    "impact": "medium",
                },
                {
                    "strategy_en": "Certified Halal transparency program",
                    "strategy_ar": "برنامج شفافية الحلال المعتمد",
                    "impact": "medium",
                },
            ],
            "retail": [
                {
                    "strategy_en": "Saudi-made products (صنع في السعودية) premium shelf",
                    "strategy_ar": "رف المنتجات السعودية المميزة",
                    "impact": "high",
                },
                {
                    "strategy_en": "Hyper-personalization via loyalty AI",
                    "strategy_ar": "التخصيص الفائق عبر برامج الولاء الذكية",
                    "impact": "high",
                },
                {
                    "strategy_en": "Instant 1-hour delivery promise",
                    "strategy_ar": "وعد التوصيل خلال ساعة واحدة",
                    "impact": "medium",
                },
            ],
            "technology": [
                {
                    "strategy_en": "Arabic-first UX and AI models",
                    "strategy_ar": "تجربة مستخدم وذكاء اصطناعي عربي أولاً",
                    "impact": "high",
                },
                {
                    "strategy_en": "Government sector integration (Yesser/Absher APIs)",
                    "strategy_ar": "تكامل مع القطاع الحكومي (ميسر/أبشر)",
                    "impact": "high",
                },
                {
                    "strategy_en": "Data sovereignty and local hosting",
                    "strategy_ar": "سيادة البيانات والاستضافة المحلية",
                    "impact": "medium",
                },
            ],
            "default": [
                {
                    "strategy_en": "Arabic-first customer experience",
                    "strategy_ar": "تجربة عملاء عربية أولاً",
                    "impact": "high",
                },
                {
                    "strategy_en": "Vision 2030 alignment branding",
                    "strategy_ar": "علامة تجارية متوافقة مع رؤية 2030",
                    "impact": "medium",
                },
                {
                    "strategy_en": "Saudization showcase (hire local, promote local)",
                    "strategy_ar": "ريادة السعودة والتوطين",
                    "impact": "medium",
                },
                {
                    "strategy_en": "Digital payment and BNPL integration",
                    "strategy_ar": "الدفع الرقمي والشراء الآن والدفع لاحقاً",
                    "impact": "medium",
                },
            ],
        }
        return {
            "sector": sector,
            "competitive_intensity": competitive_intensity,
            "strategies": strategies.get(sector.lower(), strategies["default"]),
            "key_success_factors": [
                "Deep understanding of Saudi consumer culture",
                "Saudization commitment (Nitaqat platinum)",
                "Digital-first operations",
                "Strong local partnerships",
                "Vision 2030 brand alignment",
            ],
        }

    def _build_user_message(self, context: dict) -> str:
        sector = context.get("sector", "default")
        city = context.get("city", "Riyadh")
        return (
            f"Conduct a full competitive analysis for this Saudi business.\n"
            f"Sector: {sector} | City: {city}\n\n"
            f"Steps:\n"
            f"1. Call map_local_competitors for {sector} in {city}.\n"
            f"2. Call analyze_competitor_pricing for {sector}.\n"
            f"3. Call generate_positioning_matrix with identified competitors.\n"
            f"4. Call suggest_differentiation based on competitive intensity.\n\n"
            f"Return JSON: competitors, competitive_intensity, differentiation_opportunities, "
            f"positioning_narrative_ar, positioning_narrative_en.\n\n"
            f"Full context:\n{json.dumps(context, ensure_ascii=False, indent=2)}"
        )
