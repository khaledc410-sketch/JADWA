"""
PnLModelingSubAgent — builds a 5-year Profit & Loss model
using SAMA rates from data_tools and sector-specific defaults.
"""

from typing import Any

from app.agents.base_agent import BaseAgent
from app.services.data_tools import get_saibor_3m, get_zakat_rate


# Sector defaults for P&L modeling
SECTOR_DEFAULTS = {
    "food_beverage": {
        "revenue_mult": 1.8,
        "cogs": 0.35,
        "opex": 0.40,
        "growth": 0.15,
    },
    "retail": {"revenue_mult": 2.0, "cogs": 0.55, "opex": 0.25, "growth": 0.12},
    "healthcare": {
        "revenue_mult": 1.5,
        "cogs": 0.30,
        "opex": 0.45,
        "growth": 0.14,
    },
    "education": {
        "revenue_mult": 1.3,
        "cogs": 0.20,
        "opex": 0.50,
        "growth": 0.10,
    },
    "technology": {
        "revenue_mult": 2.5,
        "cogs": 0.15,
        "opex": 0.55,
        "growth": 0.25,
    },
    "franchise": {
        "revenue_mult": 2.2,
        "cogs": 0.38,
        "opex": 0.35,
        "growth": 0.13,
    },
    "real_estate": {
        "revenue_mult": 0.12,
        "cogs": 0.50,
        "opex": 0.15,
        "growth": 0.07,
    },
    "manufacturing": {
        "revenue_mult": 1.6,
        "cogs": 0.60,
        "opex": 0.20,
        "growth": 0.10,
    },
    "logistics": {
        "revenue_mult": 1.8,
        "cogs": 0.45,
        "opex": 0.30,
        "growth": 0.13,
    },
    "hospitality": {
        "revenue_mult": 1.4,
        "cogs": 0.35,
        "opex": 0.40,
        "growth": 0.16,
    },
}

DEFAULT_SECTOR = {"revenue_mult": 1.8, "cogs": 0.40, "opex": 0.35, "growth": 0.12}


class PnLModelingSubAgent(BaseAgent):
    name: str = "PnLModelingSubAgent"
    description: str = "Builds 5-year P&L projections for Saudi SMEs"
    max_tokens: int = 2000
    temperature: float = 0.2

    @property
    def system_prompt(self) -> str:
        return (
            "أنت خبير نمذجة مالية متخصص في بناء قوائم الأرباح والخسائر للمنشآت "
            "الصغيرة والمتوسطة في المملكة العربية السعودية.\n\n"
            "You are a financial modeling specialist for Saudi SME P&L projections.\n\n"
            "Your responsibilities:\n"
            "- Build conservative 5-year P&L models using sector-specific assumptions.\n"
            "- Year 1 reflects ramp-up at 65% of full capacity.\n"
            "- Use current SAIBOR rate for interest expense (40% debt assumed).\n"
            "- Apply 2.5% Zakat on positive earnings before tax.\n"
            "- Use 10% straight-line depreciation on total investment.\n"
            "- All values in SAR.\n"
            "- Return a JSON object with: pnl_5yr (array), assumptions (object).\n"
            "  No text outside the JSON block."
        )

    @property
    def tools(self) -> list:
        return [
            {
                "name": "build_pnl_model",
                "description": (
                    "Builds a 5-year Profit & Loss model from investment and revenue assumptions. "
                    "Returns yearly revenue, COGS, gross profit, OPEX, EBITDA, Zakat, net profit."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "investment_sar": {"type": "number"},
                        "sector": {"type": "string"},
                        "annual_revenue_yr1": {"type": "number"},
                        "cogs_pct": {
                            "type": "number",
                            "description": "COGS as % of revenue (0-1)",
                        },
                        "opex_pct": {
                            "type": "number",
                            "description": "OPEX as % of revenue (0-1)",
                        },
                        "growth_rate": {
                            "type": "number",
                            "description": "Annual revenue growth rate (0-1)",
                        },
                    },
                    "required": ["investment_sar", "sector"],
                },
            },
        ]

    def execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        if tool_name == "build_pnl_model":
            return self._build_pnl_model(**tool_input)
        raise NotImplementedError(f"Unknown tool: {tool_name}")

    def _build_pnl_model(
        self,
        investment_sar: float,
        sector: str,
        annual_revenue_yr1: float = None,
        cogs_pct: float = None,
        opex_pct: float = None,
        growth_rate: float = None,
    ) -> dict:
        # Fetch live rates from data_tools
        saibor_rate = get_saibor_3m()
        zakat_rate = get_zakat_rate()

        # Sector defaults
        defaults = SECTOR_DEFAULTS.get(sector.lower(), DEFAULT_SECTOR)

        rev_yr1 = annual_revenue_yr1 or round(investment_sar * defaults["revenue_mult"])
        cogs_r = cogs_pct if cogs_pct is not None else defaults["cogs"]
        opex_r = opex_pct if opex_pct is not None else defaults["opex"]
        g_rate = growth_rate if growth_rate is not None else defaults["growth"]

        ramp_factors = [0.65, 1.0, 1.0, 1.0, 1.0]  # Year 1 ramp-up
        pnl = []
        for i in range(5):
            yr = i + 1
            rev = round(rev_yr1 * ((1 + g_rate) ** i) * ramp_factors[i])
            cogs_val = round(rev * cogs_r)
            gross_profit = rev - cogs_val
            opex_val = round(rev * opex_r)
            ebitda = gross_profit - opex_val
            dep = round(investment_sar * 0.10)  # 10% straight-line depreciation
            ebit = ebitda - dep
            interest = round(investment_sar * 0.40 * saibor_rate)  # 40% debt assumed
            ebt = ebit - interest
            zakat = round(max(ebt, 0) * zakat_rate)
            net_profit = ebt - zakat
            pnl.append(
                {
                    "year": yr,
                    "revenue": rev,
                    "cogs": cogs_val,
                    "gross_profit": gross_profit,
                    "gross_margin_pct": round(gross_profit / rev * 100, 1)
                    if rev
                    else 0,
                    "opex": opex_val,
                    "ebitda": ebitda,
                    "depreciation": dep,
                    "ebit": ebit,
                    "interest_expense": interest,
                    "ebt": ebt,
                    "zakat": zakat,
                    "net_profit": net_profit,
                    "net_margin_pct": round(net_profit / rev * 100, 1) if rev else 0,
                }
            )
        return {
            "pnl_5yr": pnl,
            "assumptions": {
                "revenue_yr1": rev_yr1,
                "cogs_pct": cogs_r,
                "opex_pct": opex_r,
                "growth_rate": g_rate,
                "saibor_rate": saibor_rate,
                "zakat_rate": zakat_rate,
            },
        }
