"""
FinancialModelingAgent — builds a full 5-year financial model:
P&L, cash flow, break-even, IRR, NPV using SAMA rates, 15% VAT, 2.5% Zakat.
"""

import json
import math
from typing import Any

from app.agents.base_agent import BaseAgent


# ---------------------------------------------------------------------------
# Saudi financial constants (mock — update with live SAMA feed later)
# ---------------------------------------------------------------------------

SAMA_SAIBOR_RATE = 0.0595  # 5.95% as of Q1 2025
VAT_RATE = 0.15  # 15% VAT (Saudi VAT since 2020)
ZAKAT_RATE = 0.025  # 2.5% on zakat base
SIDF_LOAN_RATE = 0.035  # SIDF concessional rate (Saudi Industrial Development Fund)
CORPORATE_DISCOUNT_RATE = 0.12  # Typical WACC for Saudi SMEs


class FinancialModelingAgent(BaseAgent):
    name: str = "FinancialModelingAgent"
    description: str = "5-year Saudi SME financial model: P&L, cash flow, IRR, NPV"
    max_tokens: int = 8192
    temperature: float = 0.2

    @property
    def system_prompt(self) -> str:
        return (
            "أنت خبير نمذجة مالية متخصص في دراسات الجدوى للمنشآت الصغيرة والمتوسطة "
            "في المملكة العربية السعودية.\n\n"
            "You are an expert financial modeler specializing in Saudi Arabia SME "
            "feasibility studies. You must:\n"
            "- Use SAMA rates (SAIBOR currently 5.95%).\n"
            "- Apply 15% VAT on applicable revenues and expenses.\n"
            "- Apply 2.5% Zakat on net assets (for Saudi/GCC-owned entities).\n"
            "- Model SIDF loan programs where applicable (concessional rate ~3.5%).\n"
            "- Build conservative, realistic 5-year projections.\n"
            "- All values in SAR (ريال سعودي).\n"
            "- Year 1 should reflect ramp-up (typically 60-70% of full capacity).\n"
            "- Include both Arabic and English narrative sections.\n"
            "- Return a JSON object matching the output schema exactly. "
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
            {
                "name": "calculate_irr_npv",
                "description": "Calculates IRR, NPV, and payback period from cash flow series.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "initial_investment_sar": {"type": "number"},
                        "cash_flows": {
                            "type": "array",
                            "items": {"type": "number"},
                            "description": "Annual free cash flows for years 1-5",
                        },
                        "discount_rate": {
                            "type": "number",
                            "description": "WACC (default 0.12)",
                        },
                    },
                    "required": ["initial_investment_sar", "cash_flows"],
                },
            },
            {
                "name": "fetch_sama_rates",
                "description": "Returns current SAMA benchmark rates (SAIBOR, repo rate, VAT).",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "rate_type": {
                            "type": "string",
                            "description": "saibor | repo | vat | all",
                        },
                    },
                    "required": [],
                },
            },
            {
                "name": "model_loan_scenarios",
                "description": (
                    "Models financing options: SIDF loan, commercial bank loan, equity-only. "
                    "Returns annual debt service schedule and effective cost of capital."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "investment_sar": {"type": "number"},
                        "equity_pct": {
                            "type": "number",
                            "description": "Equity portion (0-1)",
                        },
                        "loan_type": {
                            "type": "string",
                            "description": "sidf | commercial | islamic",
                        },
                        "loan_term_years": {"type": "integer"},
                    },
                    "required": ["investment_sar"],
                },
            },
            {
                "name": "calculate_break_even",
                "description": "Calculates break-even revenue and month from fixed/variable cost structure.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "fixed_costs_monthly_sar": {"type": "number"},
                        "variable_cost_pct": {"type": "number"},
                        "avg_monthly_revenue_sar": {"type": "number"},
                    },
                    "required": ["fixed_costs_monthly_sar", "variable_cost_pct"],
                },
            },
        ]

    # ------------------------------------------------------------------
    # Tool implementations
    # ------------------------------------------------------------------

    def execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        if tool_name == "build_pnl_model":
            return self._build_pnl_model(**tool_input)
        if tool_name == "calculate_irr_npv":
            return self._calculate_irr_npv(**tool_input)
        if tool_name == "fetch_sama_rates":
            return self._fetch_sama_rates(**tool_input)
        if tool_name == "model_loan_scenarios":
            return self._model_loan_scenarios(**tool_input)
        if tool_name == "calculate_break_even":
            return self._calculate_break_even(**tool_input)
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
        # Sector defaults
        sector_defaults = {
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
        defaults = sector_defaults.get(
            sector.lower(),
            {"revenue_mult": 1.8, "cogs": 0.40, "opex": 0.35, "growth": 0.12},
        )

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
            interest = round(
                investment_sar * 0.40 * SAMA_SAIBOR_RATE
            )  # 40% debt assumed
            ebt = ebit - interest
            zakat = round(max(ebt, 0) * ZAKAT_RATE)
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
            },
        }

    def _calculate_irr_npv(
        self,
        initial_investment_sar: float,
        cash_flows: list,
        discount_rate: float = CORPORATE_DISCOUNT_RATE,
    ) -> dict:
        # NPV
        npv = -initial_investment_sar
        for i, cf in enumerate(cash_flows):
            npv += cf / ((1 + discount_rate) ** (i + 1))

        # IRR via Newton-Raphson
        def _npv(rate, flows):
            return -initial_investment_sar + sum(
                cf / ((1 + rate) ** (i + 1)) for i, cf in enumerate(flows)
            )

        rate = 0.20
        for _ in range(200):
            f = _npv(rate, cash_flows)
            df_dr = sum(
                -((i + 1) * cf) / ((1 + rate) ** (i + 2))
                for i, cf in enumerate(cash_flows)
            )
            if df_dr == 0:
                break
            new_rate = rate - f / df_dr
            if abs(new_rate - rate) < 1e-8:
                rate = new_rate
                break
            rate = new_rate
        irr = round(rate, 4)

        # Payback period (months)
        cumulative = -initial_investment_sar
        payback_months = None
        for i, cf in enumerate(cash_flows):
            monthly_cf = cf / 12
            for m in range(12):
                cumulative += monthly_cf
                if cumulative >= 0 and payback_months is None:
                    payback_months = i * 12 + m + 1

        return {
            "irr": irr,
            "npv_sar": round(npv),
            "payback_period_months": payback_months or 60,
            "discount_rate_used": discount_rate,
        }

    def _fetch_sama_rates(self, rate_type: str = "all") -> dict:
        rates = {
            "saibor_3m": SAMA_SAIBOR_RATE,
            "repo_rate": 0.0600,
            "reverse_repo_rate": 0.0575,
            "vat_rate": VAT_RATE,
            "zakat_rate": ZAKAT_RATE,
            "sidf_concessional_rate": SIDF_LOAN_RATE,
            "as_of": "2025-Q1",
            "source": "SAMA (Saudi Central Bank)",
        }
        if rate_type == "all":
            return rates
        return {rate_type: rates.get(rate_type, "N/A"), "source": "SAMA"}

    def _model_loan_scenarios(
        self,
        investment_sar: float,
        equity_pct: float = 0.40,
        loan_type: str = "sidf",
        loan_term_years: int = 7,
    ) -> dict:
        debt_pct = 1 - equity_pct
        loan_amount = investment_sar * debt_pct
        rate_map = {
            "sidf": SIDF_LOAN_RATE,
            "commercial": SAMA_SAIBOR_RATE + 0.025,
            "islamic": 0.048,
        }
        rate = rate_map.get(loan_type, SAMA_SAIBOR_RATE)

        # Annuity payment
        monthly_rate = rate / 12
        n_months = loan_term_years * 12
        if monthly_rate > 0:
            monthly_payment = (
                loan_amount
                * (monthly_rate * (1 + monthly_rate) ** n_months)
                / ((1 + monthly_rate) ** n_months - 1)
            )
        else:
            monthly_payment = loan_amount / n_months

        annual_debt_service = round(monthly_payment * 12)
        schedule = []
        balance = loan_amount
        for yr in range(1, min(loan_term_years, 5) + 1):
            interest = round(balance * rate)
            principal = annual_debt_service - interest
            balance = max(balance - principal, 0)
            schedule.append(
                {
                    "year": yr,
                    "annual_payment_sar": annual_debt_service,
                    "interest_sar": interest,
                    "principal_sar": principal,
                    "closing_balance_sar": round(balance),
                }
            )

        return {
            "loan_amount_sar": round(loan_amount),
            "equity_amount_sar": round(investment_sar * equity_pct),
            "loan_type": loan_type,
            "interest_rate": rate,
            "term_years": loan_term_years,
            "annual_debt_service_sar": annual_debt_service,
            "schedule": schedule,
        }

    def _calculate_break_even(
        self,
        fixed_costs_monthly_sar: float,
        variable_cost_pct: float,
        avg_monthly_revenue_sar: float = None,
    ) -> dict:
        # Break-even revenue = Fixed Costs / (1 - Variable Cost %)
        be_revenue_monthly = fixed_costs_monthly_sar / (1 - variable_cost_pct)
        be_revenue_annual = be_revenue_monthly * 12

        if avg_monthly_revenue_sar:
            # How many months until break-even (simple cash accumulation)
            monthly_contribution = (
                avg_monthly_revenue_sar * (1 - variable_cost_pct)
                - fixed_costs_monthly_sar
            )
            if monthly_contribution > 0:
                be_month = math.ceil(fixed_costs_monthly_sar / monthly_contribution)
            else:
                be_month = None
        else:
            be_month = None

        return {
            "break_even_revenue_monthly_sar": round(be_revenue_monthly),
            "break_even_revenue_annual_sar": round(be_revenue_annual),
            "break_even_month": be_month,
            "fixed_costs_monthly_sar": fixed_costs_monthly_sar,
            "contribution_margin_pct": round((1 - variable_cost_pct) * 100, 1),
        }

    def _build_user_message(self, context: dict) -> str:
        sector = context.get("sector", "default")
        investment = context.get("investment_amount_sar", 2_000_000)
        return (
            f"Build a complete 5-year financial model for this Saudi business.\n"
            f"Sector: {sector} | Investment: SAR {investment:,.0f}\n\n"
            f"Steps:\n"
            f"1. Call fetch_sama_rates to get current SAMA rates.\n"
            f"2. Call model_loan_scenarios with 40% equity, SIDF loan, 7-year term.\n"
            f"3. Call build_pnl_model using the investment amount and sector.\n"
            f"4. Extract annual net cash flows from P&L (net_profit + depreciation - capex 10% yr1).\n"
            f"5. Call calculate_irr_npv with those cash flows.\n"
            f"6. Call calculate_break_even using Year 1 opex as fixed costs and COGS% as variable.\n\n"
            f"Return a JSON object with: pnl_5yr, cash_flow_5yr, break_even_month, irr, "
            f"npv_sar, payback_period_months, narrative_ar, narrative_en.\n\n"
            f"Full context:\n{json.dumps(context, ensure_ascii=False, indent=2)}"
        )
