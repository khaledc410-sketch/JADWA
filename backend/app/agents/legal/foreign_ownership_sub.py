"""
ForeignOwnershipSubAgent — MISA foreign ownership rules, minimum capital,
and negative-list sectors.
"""

from typing import Any

from app.agents.base_agent import BaseAgent
from app.services.data_tools import load_seed


# Ownership restriction data (mirrors original LegalRegulatoryAgent logic)
_FOREIGN_OWNERSHIP_RULES = {
    "real_estate": {
        "allowed": True,
        "min_capital_sar": 30_000_000,
        "misa_required": True,
    },
    "retail": {
        "allowed": True,
        "min_capital_sar": 26_000_000,
        "misa_required": True,
    },
    "media": {
        "allowed": False,
        "min_capital_sar": 0,
        "misa_required": True,
    },
}

_DEFAULT_RULE = {
    "allowed": True,
    "min_capital_sar": 500_000,
    "misa_required": True,
}


class ForeignOwnershipSubAgent(BaseAgent):
    name: str = "ForeignOwnershipSubAgent"
    description: str = (
        "MISA foreign ownership rules, minimum capital requirements, "
        "negative list, and investment licensing for non-Saudi investors"
    )
    temperature: float = 0.2

    @property
    def system_prompt(self) -> str:
        return (
            "أنت خبير في نظام الاستثمار الأجنبي في المملكة العربية السعودية ومتطلبات وزارة الاستثمار (MISA).\n\n"
            "You are a MISA and foreign investment regulation expert covering:\n"
            "- Foreign Investment Law (نظام الاستثمار الأجنبي)\n"
            "- MISA licensing requirements and costs\n"
            "- Minimum capital requirements per sector\n"
            "- Negative list: sectors closed or restricted for foreign investors\n"
            "- Ownership structures: 100% foreign, JV, branch office\n"
            "- GCC national treatment exemptions\n\n"
            "For each query:\n"
            "- State whether foreign ownership is allowed in the sector.\n"
            "- List MISA license cost and timeline.\n"
            "- Specify minimum capital in SAR.\n"
            "- Flag negative-list sectors clearly.\n"
            "- Provide bilingual output (Arabic and English).\n\n"
            "Return a JSON object with: sector, investor_nationality, "
            "foreign_ownership_allowed, requires_misa_licence, misa_licence_cost_sar, "
            "misa_licence_days, min_capital_sar, negative_list."
        )

    @property
    def tools(self) -> list:
        return [
            {
                "name": "check_foreign_ownership_rules",
                "description": (
                    "Checks foreign ownership rules, MISA requirements, negative list sectors, "
                    "and minimum capital requirements for non-Saudi investors."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sector": {
                            "type": "string",
                            "description": "Business sector to check ownership rules for",
                        },
                        "ownership_type": {
                            "type": "string",
                            "description": "Ownership structure: full_foreign | joint_venture | branch_office | gcc_national",
                        },
                    },
                    "required": ["sector"],
                },
            },
        ]

    def execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        if tool_name == "check_foreign_ownership_rules":
            return self._check_foreign_ownership_rules(**tool_input)
        raise NotImplementedError(f"Unknown tool: {tool_name}")

    def _check_foreign_ownership_rules(
        self, sector: str, ownership_type: str = "full_foreign"
    ) -> dict:
        sector_lower = sector.lower()
        is_saudi = ownership_type.lower() in ("saudi", "sa", "local")

        rule = _FOREIGN_OWNERSHIP_RULES.get(sector_lower, _DEFAULT_RULE)

        requires_misa = rule["misa_required"] and not is_saudi

        return {
            "sector": sector,
            "ownership_type": ownership_type,
            "foreign_ownership_allowed": rule["allowed"],
            "requires_misa_licence": requires_misa,
            "misa_licence_cost_sar": 10_000 if requires_misa else 0,
            "misa_licence_days": 30 if requires_misa else 0,
            "min_capital_sar": rule["min_capital_sar"] if not is_saudi else 0,
            "negative_list": sector_lower in ["media"],
            "notes": (
                "Sector is on the negative list — foreign investment not permitted."
                if sector_lower in ["media"]
                else "MISA license required before Commercial Registration."
                if requires_misa
                else "No MISA requirements for local investors."
            ),
        }

    def _build_user_message(self, context: dict) -> str:
        sector = context.get("sector", "default")
        nationality = context.get("investor_nationality", "SA")
        ownership = context.get("ownership_type", "full_foreign")
        if nationality.upper() != "SA":
            ownership = ownership if ownership != "full_foreign" else "full_foreign"
        return (
            f"Check foreign ownership rules and MISA requirements.\n"
            f"Sector: {sector} | Investor nationality: {nationality} | "
            f"Ownership type: {ownership}\n\n"
            f"Call check_foreign_ownership_rules with sector '{sector}' "
            f"and ownership_type '{ownership}'.\n"
            f"Return JSON with: sector, ownership_type, foreign_ownership_allowed, "
            f"requires_misa_licence, misa_licence_cost_sar, misa_licence_days, "
            f"min_capital_sar, negative_list, notes."
        )
