"""
MarketSizingSubAgent — TAM/SAM/SOM calculations, sector growth, and CAGR projections.
Sources: GASTAT sector data and Saudi market seed data.
"""

from typing import Any

from app.agents.base_agent import BaseAgent
from app.services.data_tools import get_market_data, load_seed


# Fallback Saudi market data (used when seed files lack sector data)
_SAUDI_MARKET_FALLBACK = {
    "retail": {
        "tam_sar": 550_000_000_000,
        "sam_sar": 82_500_000_000,
        "growth_cagr_5yr": 0.07,
    },
    "food_beverage": {
        "tam_sar": 110_000_000_000,
        "sam_sar": 16_500_000_000,
        "growth_cagr_5yr": 0.09,
    },
    "fnb": {
        "tam_sar": 110_000_000_000,
        "sam_sar": 16_500_000_000,
        "growth_cagr_5yr": 0.09,
    },
    "healthcare": {
        "tam_sar": 145_000_000_000,
        "sam_sar": 43_500_000_000,
        "growth_cagr_5yr": 0.11,
    },
    "education": {
        "tam_sar": 60_000_000_000,
        "sam_sar": 12_000_000_000,
        "growth_cagr_5yr": 0.08,
    },
    "technology": {
        "tam_sar": 95_000_000_000,
        "sam_sar": 19_000_000_000,
        "growth_cagr_5yr": 0.18,
    },
    "real_estate": {
        "tam_sar": 700_000_000_000,
        "sam_sar": 210_000_000_000,
        "growth_cagr_5yr": 0.06,
    },
    "franchise": {
        "tam_sar": 55_000_000_000,
        "sam_sar": 11_000_000_000,
        "growth_cagr_5yr": 0.12,
    },
    "manufacturing": {
        "tam_sar": 320_000_000_000,
        "sam_sar": 64_000_000_000,
        "growth_cagr_5yr": 0.10,
    },
    "logistics": {
        "tam_sar": 75_000_000_000,
        "sam_sar": 22_500_000_000,
        "growth_cagr_5yr": 0.13,
    },
    "hospitality": {
        "tam_sar": 90_000_000_000,
        "sam_sar": 27_000_000_000,
        "growth_cagr_5yr": 0.16,
    },
    "default": {
        "tam_sar": 100_000_000_000,
        "sam_sar": 15_000_000_000,
        "growth_cagr_5yr": 0.08,
    },
}


class MarketSizingSubAgent(BaseAgent):
    name: str = "MarketSizingSubAgent"
    description: str = (
        "TAM/SAM/SOM calculations, sector growth rates, and CAGR projections"
    )

    @property
    def system_prompt(self) -> str:
        return (
            "You are a market sizing specialist for Saudi Arabia sectors. "
            "You calculate TAM (Total Addressable Market), SAM (Serviceable "
            "Addressable Market), and SOM (Serviceable Obtainable Market) using "
            "top-down and bottom-up methodologies.\n\n"
            "Instructions:\n"
            "- TAM = total Saudi market for the sector.\n"
            "- SAM = serviceable addressable market (realistic geographic/demographic slice).\n"
            "- SOM = serviceable obtainable market (realistic first 3-year capture).\n"
            "- Provide 5-year CAGR projections based on Vision 2030 targets.\n"
            "- All monetary values in SAR with USD equivalents (1 USD = 3.75 SAR).\n"
            "- Include growth drivers and methodology notes.\n"
            "- Return a single JSON object. No text outside the JSON block."
        )

    @property
    def tools(self) -> list:
        return [
            {
                "name": "calculate_tam_sam_som",
                "description": (
                    "Calculates TAM, SAM, and SOM values for a given sector "
                    "using bottom-up and top-down methodologies based on "
                    "investment size and sector data."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "investment_sar": {
                            "type": "number",
                            "description": "Investment amount in SAR",
                        },
                        "sector": {
                            "type": "string",
                            "description": "Business sector (e.g. retail, healthcare)",
                        },
                    },
                    "required": ["sector"],
                },
            },
            {
                "name": "fetch_sector_growth_data",
                "description": (
                    "Retrieves historical growth rates and 5-year CAGR projections "
                    "for a Saudi sector from Vision 2030 and industry reports."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sector": {"type": "string"},
                        "years": {
                            "type": "integer",
                            "description": "Projection years (default 5)",
                        },
                    },
                    "required": ["sector"],
                },
            },
        ]

    def execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        if tool_name == "calculate_tam_sam_som":
            return self._calculate_tam_sam_som(**tool_input)
        if tool_name == "fetch_sector_growth_data":
            return self._fetch_sector_growth_data(**tool_input)
        raise NotImplementedError(f"Unknown tool: {tool_name}")

    def _get_sector_data(self, sector: str) -> dict:
        """Try seed data first, fall back to hardcoded defaults."""
        seed = get_market_data(sector)
        if seed and isinstance(seed, dict) and seed.get("tam_sar"):
            return seed
        return _SAUDI_MARKET_FALLBACK.get(
            sector.lower(), _SAUDI_MARKET_FALLBACK["default"]
        )

    def _calculate_tam_sam_som(
        self, sector: str, investment_sar: float = 1_000_000, **kwargs
    ) -> dict:
        data = self._get_sector_data(sector)
        tam = data["tam_sar"]
        sam = data["sam_sar"]
        # SOM: realistic 3-year penetration based on investment size
        penetration = min(investment_sar / sam * 15, 0.05)  # cap at 5%
        som = sam * penetration

        return {
            "sector": sector,
            "tam_sar": tam,
            "sam_sar": sam,
            "som_sar": round(som),
            "tam_usd": round(tam / 3.75),
            "sam_usd": round(sam / 3.75),
            "som_usd": round(som / 3.75),
            "methodology": "Top-down (GASTAT + sector reports) + Bottom-up (investment-scaled)",
        }

    def _fetch_sector_growth_data(self, sector: str, years: int = 5) -> dict:
        data = self._get_sector_data(sector)
        cagr = data.get("growth_cagr_5yr", 0.08)
        sam = data["sam_sar"]
        projections = []
        for yr in range(1, years + 1):
            projections.append(
                {
                    "year": 2024 + yr - 1,
                    "market_size_sar": round(sam * ((1 + cagr) ** yr)),
                }
            )
        return {
            "sector": sector,
            "cagr_5yr": cagr,
            "projections": projections,
            "drivers": [
                "Vision 2030 sector development targets",
                "Growing Saudi middle class",
                "Digital transformation initiative",
                "Rising tourist inflows",
                "Government SME support programs",
            ],
        }

    def _build_user_message(self, context: dict) -> str:
        sector = context.get("sector", "default")
        city = context.get("city", "Riyadh")
        investment = context.get("investment_amount_sar", 1_000_000)

        return (
            f"Calculate market sizing for this project.\n"
            f"Sector: {sector} | City: {city} | Investment: SAR {investment:,.0f}\n\n"
            f"Steps:\n"
            f"1. Call calculate_tam_sam_som for sector='{sector}' with "
            f"investment_sar={investment}.\n"
            f"2. Call fetch_sector_growth_data for sector='{sector}'.\n\n"
            f"Return JSON with: tam, sam, som (SAR and USD), cagr_5yr, "
            f"projections, methodology, growth_drivers."
        )
