"""
FinancialOrchestrator — runs all financial sub-agents in parallel,
then synthesizes into a complete 5-year financial model.
"""

import json
from typing import Any

from app.agents.base_agent import SubAgentOrchestrator
from app.agents.financial.sama_rates_sub import SAMARatesSubAgent
from app.agents.financial.pnl_modeling_sub import PnLModelingSubAgent
from app.agents.financial.loan_scenario_sub import LoanScenarioSubAgent
from app.agents.financial.investment_analysis_sub import InvestmentAnalysisSubAgent


class FinancialOrchestrator(SubAgentOrchestrator):
    name: str = "FinancialModelingAgent"
    description: str = "5-year Saudi SME financial model: P&L, cash flow, IRR, NPV"
    max_tokens: int = 8192
    reviewer_max_tokens: int = 8192
    reviewer_temperature: float = 0.2

    def get_sub_agents(self, context: dict) -> list:
        return [
            SAMARatesSubAgent(db=self.db, run_id=self.run_id),
            PnLModelingSubAgent(db=self.db, run_id=self.run_id),
            LoanScenarioSubAgent(db=self.db, run_id=self.run_id),
            InvestmentAnalysisSubAgent(db=self.db, run_id=self.run_id),
        ]

    @property
    def reviewer_system_prompt(self) -> str:
        return (
            "أنت محلل مالي سعودي خبير تقوم بدمج مخرجات عدة وكلاء فرعيين في نموذج مالي "
            "متكامل لدراسة الجدوى.\n\n"
            "You are an expert Saudi financial analyst who synthesizes outputs from "
            "multiple specialized sub-agents into a single, cohesive financial model.\n\n"
            "You will receive outputs from:\n"
            "1. SAMARatesSubAgent — SAMA rates, tax rates, SIDF programs\n"
            "2. PnLModelingSubAgent — 5-year P&L projections\n"
            "3. LoanScenarioSubAgent — financing scenarios and debt schedules\n"
            "4. InvestmentAnalysisSubAgent — IRR, NPV, break-even analysis\n\n"
            "Your responsibilities:\n"
            "- Cross-validate all sub-agent outputs for consistency.\n"
            "- Resolve any conflicts by choosing the most reliable data.\n"
            "- Derive cash_flow_5yr from P&L (net_profit + depreciation).\n"
            "- Ensure IRR/NPV are consistent with the P&L cash flows.\n"
            "- Produce bilingual narratives (Arabic and English).\n\n"
            "Return a JSON object with exactly these keys:\n"
            "  pnl_5yr, cash_flow_5yr, break_even, irr, npv,\n"
            "  narrative_ar, narrative_en\n\n"
            "No text outside the JSON block."
        )

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
