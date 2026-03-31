"""
LoanScenarioSubAgent — models SIDF, commercial, and Islamic loan options
for Saudi SME financing scenarios.
"""

from typing import Any

from app.agents.base_agent import BaseAgent
from app.services.data_tools import (
    get_sama_rates,
    get_saibor_3m,
    get_sidf_programs,
)


class LoanScenarioSubAgent(BaseAgent):
    name: str = "LoanScenarioSubAgent"
    description: str = "Models SIDF, commercial bank, and Islamic financing scenarios"
    max_tokens: int = 4096
    temperature: float = 0.2

    @property
    def system_prompt(self) -> str:
        return (
            "أنت خبير في التمويل السعودي متخصص في برامج صندوق التنمية الصناعية "
            "والبنوك التجارية والتمويل الإسلامي.\n\n"
            "You are a Saudi financing expert specializing in:\n"
            "- SIDF (Saudi Industrial Development Fund) concessional loan programs.\n"
            "- Commercial bank lending at SAIBOR + spread.\n"
            "- Islamic finance structures (Murabaha, Ijara, Istisna).\n\n"
            "Your responsibilities:\n"
            "- Model multiple financing scenarios with amortization schedules.\n"
            "- Compare effective cost of capital across loan types.\n"
            "- Provide SIDF program eligibility details.\n"
            "- All values in SAR.\n"
            "- Return a JSON object with: loan_scenarios (array of scenario objects), "
            "sidf_programs (array).\n"
            "  No text outside the JSON block."
        )

    @property
    def tools(self) -> list:
        return [
            {
                "name": "model_loan_scenarios",
                "description": (
                    "Models financing options: SIDF loan, commercial bank loan, Islamic finance. "
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
                "name": "fetch_sidf_programs",
                "description": (
                    "Returns available SIDF loan programs with eligibility criteria, "
                    "interest rates, and maximum terms."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        ]

    def execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        if tool_name == "model_loan_scenarios":
            return self._model_loan_scenarios(**tool_input)
        if tool_name == "fetch_sidf_programs":
            return self._fetch_sidf_programs()
        raise NotImplementedError(f"Unknown tool: {tool_name}")

    def _model_loan_scenarios(
        self,
        investment_sar: float,
        equity_pct: float = 0.40,
        loan_type: str = "sidf",
        loan_term_years: int = 7,
    ) -> dict:
        # Fetch live rates from data_tools
        saibor_rate = get_saibor_3m()
        sama_data = get_sama_rates()

        # Determine SIDF concessional rate from seed data
        sidf_programs = get_sidf_programs()
        sidf_rate = 0.035  # fallback
        if sidf_programs:
            for prog in sidf_programs:
                rate = prog.get("interest_rate_percent") or prog.get("rate_percent")
                if rate:
                    sidf_rate = rate / 100
                    break

        debt_pct = 1 - equity_pct
        loan_amount = investment_sar * debt_pct
        rate_map = {
            "sidf": sidf_rate,
            "commercial": saibor_rate + 0.025,
            "islamic": 0.048,
        }
        rate = rate_map.get(loan_type, saibor_rate)

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

    def _fetch_sidf_programs(self) -> dict:
        programs = get_sidf_programs()
        return {
            "sidf_programs": programs,
            "source": "SAMA / SIDF seed data",
        }
