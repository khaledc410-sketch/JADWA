"""
SAMARatesSubAgent — fetches SAMA/SAIBOR rates, VAT, Zakat, and SIDF programs.
"""

from typing import Any

from app.agents.base_agent import BaseAgent
from app.services.data_tools import (
    get_sama_rates,
    get_saibor_3m,
    get_vat_rate,
    get_zakat_rate,
    get_sidf_programs,
)


class SAMARatesSubAgent(BaseAgent):
    name: str = "SAMARatesSubAgent"
    description: str = "Fetches SAMA rates, SAIBOR, VAT, Zakat, and SIDF loan programs"
    max_tokens: int = 4096
    temperature: float = 0.1

    @property
    def system_prompt(self) -> str:
        return (
            "أنت متخصص في السياسة النقدية السعودية ومعدلات البنك المركزي السعودي (ساما).\n\n"
            "You are a Saudi monetary policy specialist with deep knowledge of SAMA "
            "(Saudi Central Bank) rates, SAIBOR benchmarks, tax regulations, and SIDF "
            "financing programs.\n\n"
            "Your responsibilities:\n"
            "- Fetch and return current SAMA benchmark rates (SAIBOR 3-month, repo, reverse repo).\n"
            "- Provide Saudi tax rates: 15% VAT, 2.5% Zakat on net assets, corporate income tax.\n"
            "- List SIDF concessional loan programs with eligibility and terms.\n"
            "- All monetary values in SAR.\n"
            "- Return a JSON object with: sama_rates, tax_rates, sidf_programs.\n"
            "  No text outside the JSON block."
        )

    @property
    def tools(self) -> list:
        return [
            {
                "name": "fetch_sama_rates",
                "description": (
                    "Returns full SAMA rates data including SAIBOR, repo rate, "
                    "reverse repo rate, and SIDF concessional rates from seed data."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "rate_type": {
                            "type": "string",
                            "description": "Filter: saibor | repo | all (default: all)",
                        },
                    },
                    "required": [],
                },
            },
            {
                "name": "fetch_tax_rates",
                "description": (
                    "Returns Saudi tax rates: VAT (15%), Zakat (2.5%), "
                    "and corporate income tax rates."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        ]

    def execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        if tool_name == "fetch_sama_rates":
            return self._fetch_sama_rates(**tool_input)
        if tool_name == "fetch_tax_rates":
            return self._fetch_tax_rates()
        raise NotImplementedError(f"Unknown tool: {tool_name}")

    def _fetch_sama_rates(self, rate_type: str = "all") -> dict:
        full_rates = get_sama_rates()
        saibor = get_saibor_3m()
        sidf = get_sidf_programs()

        rates = {
            "saibor_3m": saibor,
            "repo_rate": full_rates.get("repo_rate", {}).get("rate_percent", 6.0) / 100
            if isinstance(full_rates.get("repo_rate"), dict)
            else 0.06,
            "reverse_repo_rate": full_rates.get("reverse_repo_rate", {}).get(
                "rate_percent", 5.75
            )
            / 100
            if isinstance(full_rates.get("reverse_repo_rate"), dict)
            else 0.0575,
            "sidf_programs": sidf,
            "source": "SAMA (Saudi Central Bank)",
            "full_data": full_rates,
        }

        if rate_type == "all":
            return rates
        return {rate_type: rates.get(rate_type, "N/A"), "source": "SAMA"}

    def _fetch_tax_rates(self) -> dict:
        return {
            "vat_rate": get_vat_rate(),
            "zakat_rate": get_zakat_rate(),
            "corporate_income_tax": 0.20,
            "notes": {
                "vat": "15% standard VAT on most goods and services since July 2020",
                "zakat": "2.5% on adjusted net income for Saudi/GCC-owned entities",
                "corporate_tax": "20% on non-Saudi/non-GCC foreign investor share of profits",
            },
        }
