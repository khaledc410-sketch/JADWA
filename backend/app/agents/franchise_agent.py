"""
FranchiseAgent — RFTA-specific franchise analysis.
Activated only when sector == 'franchise'.
"""

import json
from typing import Any

from app.agents.base_agent import BaseAgent


# ---------------------------------------------------------------------------
# RFTA franchise database (mock — real RFTA API integration later)
# ---------------------------------------------------------------------------

_FRANCHISE_DB = {
    "subway": {
        "name_en": "Subway",
        "name_ar": "ساب واي",
        "rfta_status": "registered",
        "category": "food_beverage",
        "franchise_fee_sar": 75_000,
        "royalty_percent": 8,
        "marketing_fee_percent": 4.5,
        "territory_rights": "non_exclusive",
        "training_weeks": 2,
        "min_investment_sar": 500_000,
        "avg_unit_revenue_sar": 1_800_000,
        "break_even_months": 24,
        "total_units_saudi": 650,
    },
    "mcdonalds": {
        "name_en": "McDonald's",
        "name_ar": "ماكدونالدز",
        "rfta_status": "registered",
        "category": "food_beverage",
        "franchise_fee_sar": 375_000,
        "royalty_percent": 5,
        "marketing_fee_percent": 4,
        "territory_rights": "exclusive",
        "training_weeks": 12,
        "min_investment_sar": 3_500_000,
        "avg_unit_revenue_sar": 8_000_000,
        "break_even_months": 36,
        "total_units_saudi": 250,
    },
    "kfc": {
        "name_en": "KFC",
        "name_ar": "كنتاكي",
        "rfta_status": "registered",
        "category": "food_beverage",
        "franchise_fee_sar": 300_000,
        "royalty_percent": 5,
        "marketing_fee_percent": 5,
        "territory_rights": "exclusive",
        "training_weeks": 8,
        "min_investment_sar": 2_500_000,
        "avg_unit_revenue_sar": 6_000_000,
        "break_even_months": 30,
        "total_units_saudi": 500,
    },
    "generic_food": {
        "name_en": "Generic Food Franchise",
        "name_ar": "امتياز غذائي نموذجي",
        "rfta_status": "registered",
        "category": "food_beverage",
        "franchise_fee_sar": 150_000,
        "royalty_percent": 6,
        "marketing_fee_percent": 3,
        "territory_rights": "exclusive",
        "training_weeks": 4,
        "min_investment_sar": 1_200_000,
        "avg_unit_revenue_sar": 2_800_000,
        "break_even_months": 22,
        "total_units_saudi": 50,
    },
}


class FranchiseAgent(BaseAgent):
    name: str = "FranchiseAgent"
    description: str = "RFTA franchise analysis, ROI modeling, compliance"
    temperature: float = 0.3

    @property
    def system_prompt(self) -> str:
        return (
            "أنت متخصص في الامتياز التجاري مع خبرة واسعة في لوائح نظام الامتياز السعودي (RFTA)، "
            "وإفصاح الامتياز، وتحليل المنطقة الجغرافية، ونمذجة العائد على الاستثمار.\n\n"
            "You are a franchise specialist with expertise in:\n"
            "- Saudi RFTA (نظام الامتياز التجاري) regulations and compliance\n"
            "- Franchise Disclosure Document (FDD) requirements\n"
            "- Territory analysis and exclusivity rights\n"
            "- Franchise ROI modeling and unit economics\n"
            "- Saudi franchise market dynamics\n\n"
            "Instructions:\n"
            "- Verify RFTA registration status of the franchisor.\n"
            "- Analyze the franchise agreement terms critically.\n"
            "- Model realistic unit economics for the Saudi market.\n"
            "- Highlight compliance risks and disclosure requirements.\n"
            "- Use both Arabic and English in narratives.\n"
            "Return a JSON object matching the output schema exactly."
        )

    @property
    def tools(self) -> list:
        return [
            {
                "name": "lookup_rfta_franchise",
                "description": (
                    "Looks up a franchise brand in the RFTA registry, returning "
                    "registration status, fee structure, and Saudi presence data."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "brand_name": {
                            "type": "string",
                            "description": "Franchise brand name in English or Arabic",
                        },
                        "sector": {"type": "string"},
                    },
                    "required": ["brand_name"],
                },
            },
            {
                "name": "analyze_franchise_agreement",
                "description": (
                    "Analyzes key franchise agreement terms: fees, royalties, territory, "
                    "renewal rights, exit clauses, and Saudi law compliance."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "brand_name": {"type": "string"},
                        "franchise_fee_sar": {"type": "number"},
                        "royalty_percent": {"type": "number"},
                        "territory_rights": {"type": "string"},
                        "term_years": {"type": "integer"},
                    },
                    "required": ["brand_name"],
                },
            },
            {
                "name": "calculate_franchise_roi",
                "description": (
                    "Calculates franchise ROI, payback period, and annual cash flow "
                    "based on unit economics and Saudi market benchmarks."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "total_investment_sar": {"type": "number"},
                        "franchise_fee_sar": {"type": "number"},
                        "royalty_percent": {"type": "number"},
                        "avg_annual_revenue_sar": {"type": "number"},
                        "cogs_percent": {"type": "number"},
                        "opex_percent": {"type": "number"},
                    },
                    "required": ["total_investment_sar", "avg_annual_revenue_sar"],
                },
            },
            {
                "name": "check_rfta_compliance",
                "description": (
                    "Checks whether the franchise structure complies with Saudi RFTA "
                    "regulations, including disclosure, territory, and Saudization requirements."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "brand_name": {"type": "string"},
                        "franchisor_nationality": {"type": "string"},
                        "disclosure_provided": {"type": "boolean"},
                    },
                    "required": ["brand_name"],
                },
            },
        ]

    # ------------------------------------------------------------------
    # Tool implementations
    # ------------------------------------------------------------------

    def execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        if tool_name == "lookup_rfta_franchise":
            return self._lookup_rfta_franchise(**tool_input)
        if tool_name == "analyze_franchise_agreement":
            return self._analyze_franchise_agreement(**tool_input)
        if tool_name == "calculate_franchise_roi":
            return self._calculate_franchise_roi(**tool_input)
        if tool_name == "check_rfta_compliance":
            return self._check_rfta_compliance(**tool_input)
        raise NotImplementedError(f"Unknown tool: {tool_name}")

    def _lookup_rfta_franchise(self, brand_name: str, sector: str = "") -> dict:
        key = brand_name.lower().replace(" ", "_").replace("'", "").replace("-", "_")
        data = _FRANCHISE_DB.get(key, _FRANCHISE_DB["generic_food"])
        return {
            "brand_name": brand_name,
            "rfta_status": data["rfta_status"],
            "rfta_registration_number": f"RFTA-{abs(hash(brand_name)) % 100000:05d}",
            "franchise_fee_sar": data["franchise_fee_sar"],
            "royalty_percent": data["royalty_percent"],
            "marketing_fee_percent": data["marketing_fee_percent"],
            "territory_rights": data["territory_rights"],
            "training_weeks": data["training_weeks"],
            "min_investment_sar": data["min_investment_sar"],
            "total_units_saudi": data["total_units_saudi"],
            "category": data.get("category", sector),
        }

    def _analyze_franchise_agreement(
        self,
        brand_name: str,
        franchise_fee_sar: float = 150_000,
        royalty_percent: float = 6,
        territory_rights: str = "exclusive",
        term_years: int = 5,
    ) -> dict:
        red_flags = []
        if royalty_percent > 10:
            red_flags.append(
                "Royalty rate exceeds 10% — unusually high for Saudi market."
            )
        if term_years < 5:
            red_flags.append("Term shorter than 5 years — limited time to achieve ROI.")
        if territory_rights == "non_exclusive":
            red_flags.append(
                "Non-exclusive territory — risk of competitor franchisees nearby."
            )

        annual_royalty_on_2m_revenue = round(2_000_000 * royalty_percent / 100)

        return {
            "brand_name": brand_name,
            "term_years": term_years,
            "franchise_fee_sar": franchise_fee_sar,
            "royalty_percent": royalty_percent,
            "territory_rights": territory_rights,
            "renewal_rights": "Yes, at franchisor's discretion",
            "exit_clause": "12-month notice with franchise fee forfeiture",
            "red_flags": red_flags,
            "annual_royalty_on_2m_revenue_sar": annual_royalty_on_2m_revenue,
            "key_obligations": [
                "Brand standards compliance",
                "Minimum performance thresholds",
                "Mandatory training completion",
                "Exclusive supply chain usage",
                "Annual audit rights for franchisor",
            ],
        }

    def _calculate_franchise_roi(
        self,
        total_investment_sar: float,
        avg_annual_revenue_sar: float,
        franchise_fee_sar: float = 150_000,
        royalty_percent: float = 6,
        cogs_percent: float = 0.35,
        opex_percent: float = 0.35,
    ) -> dict:
        gross_profit = avg_annual_revenue_sar * (1 - cogs_percent)
        royalty_cost = avg_annual_revenue_sar * (royalty_percent / 100)
        marketing_cost = avg_annual_revenue_sar * 0.03
        net_operating_income = (
            gross_profit
            - (avg_annual_revenue_sar * opex_percent)
            - royalty_cost
            - marketing_cost
        )
        annual_roi_pct = round((net_operating_income / total_investment_sar) * 100, 1)
        payback_months = (
            round((total_investment_sar / net_operating_income) * 12)
            if net_operating_income > 0
            else None
        )

        return {
            "total_investment_sar": total_investment_sar,
            "avg_annual_revenue_sar": avg_annual_revenue_sar,
            "gross_profit_sar": round(gross_profit),
            "annual_royalty_sar": round(royalty_cost),
            "net_operating_income_sar": round(net_operating_income),
            "annual_roi_percent": annual_roi_pct,
            "payback_period_months": payback_months,
            "year1_net_profit_sar": round(
                net_operating_income * 0.65
            ),  # Year 1 ramp-up
            "year3_net_profit_sar": round(net_operating_income * 1.10),
        }

    def _check_rfta_compliance(
        self,
        brand_name: str,
        franchisor_nationality: str = "US",
        disclosure_provided: bool = True,
    ) -> dict:
        issues = []
        if not disclosure_provided:
            issues.append(
                "Franchise Disclosure Document (FDD) not provided — mandatory under RFTA."
            )
        if franchisor_nationality not in ["SA", "GCC"]:
            issues.append(
                "Foreign franchisor must register with MCI before signing agreements."
            )

        return {
            "brand_name": brand_name,
            "rfta_compliant": len(issues) == 0,
            "compliance_issues": issues,
            "required_documents": [
                "Franchise Disclosure Document (FDD) in Arabic",
                "Franchisor Commercial Registration (CR) copy",
                "Franchise Agreement (signed by both parties)",
                "Territory map and exclusivity documentation",
                "Training schedule and operations manual",
            ],
            "fdd_waiting_period_days": 14,
            "registration_cost_sar": 5_000,
            "registration_timeline_days": 30,
        }

    def _build_user_message(self, context: dict) -> str:
        brand = context.get(
            "franchise_brand", context.get("business_name", "Generic Franchise")
        )
        investment = context.get("investment_amount_sar", 1_500_000)
        return (
            f"Conduct a full RFTA franchise analysis for: {brand}\n"
            f"Investment: SAR {investment:,.0f}\n\n"
            f"Steps:\n"
            f"1. Call lookup_rfta_franchise for brand '{brand}'.\n"
            f"2. Call analyze_franchise_agreement with the returned terms.\n"
            f"3. Call calculate_franchise_roi using investment and expected revenue.\n"
            f"4. Call check_rfta_compliance for regulatory conformance.\n\n"
            f"Return JSON: rfta_status, franchise_fee_sar, royalty_percent, territory_rights, "
            f"training_weeks, franchisor_support, unit_economics, narrative_ar, narrative_en.\n\n"
            f"Full context:\n{json.dumps(context, ensure_ascii=False, indent=2)}"
        )
