"""
InvestmentAnalysisSubAgent — calculates IRR, NPV, payback period,
and break-even analysis for Saudi feasibility studies.
"""

import math
from typing import Any

from app.agents.base_agent import BaseAgent


CORPORATE_DISCOUNT_RATE = 0.12  # Typical WACC for Saudi SMEs


class InvestmentAnalysisSubAgent(BaseAgent):
    name: str = "InvestmentAnalysisSubAgent"
    description: str = "IRR, NPV, payback period, and break-even calculations"
    max_tokens: int = 4096
    temperature: float = 0.2

    @property
    def system_prompt(self) -> str:
        return (
            "أنت متخصص في تحليل الاستثمار ودراسات الجدوى للمشاريع السعودية.\n\n"
            "You are an investment analysis specialist for Saudi feasibility studies.\n\n"
            "Your responsibilities:\n"
            "- Calculate Internal Rate of Return (IRR) using Newton-Raphson method.\n"
            "- Calculate Net Present Value (NPV) at the project's WACC.\n"
            "- Determine payback period in months.\n"
            "- Perform break-even analysis (revenue and month).\n"
            "- Use 12% WACC as default discount rate for Saudi SMEs.\n"
            "- All values in SAR.\n"
            "- Return a JSON object with: irr, npv_sar, payback_period_months, "
            "break_even_revenue_monthly_sar, break_even_month.\n"
            "  No text outside the JSON block."
        )

    @property
    def tools(self) -> list:
        return [
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

    def execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        if tool_name == "calculate_irr_npv":
            return self._calculate_irr_npv(**tool_input)
        if tool_name == "calculate_break_even":
            return self._calculate_break_even(**tool_input)
        raise NotImplementedError(f"Unknown tool: {tool_name}")

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
