"""
LicensingSubAgent — MCI licenses, costs, and timelines per sector.
"""

from typing import Any

from app.agents.base_agent import BaseAgent
from app.services.data_tools import get_licenses, normalize_sector


class LicensingSubAgent(BaseAgent):
    name: str = "LicensingSubAgent"
    description: str = (
        "MCI commercial licensing: required licenses, costs in SAR, "
        "processing timelines, and issuing authorities per sector"
    )
    temperature: float = 0.2

    @property
    def system_prompt(self) -> str:
        return (
            "أنت متخصص في التراخيص التجارية السعودية ونظام السجل التجاري.\n\n"
            "You are a Saudi commercial licensing specialist covering:\n"
            "- MCI (وزارة التجارة): Commercial Registration (CR), trade licenses\n"
            "- Balady (بلدي): Municipality permits for physical locations\n"
            "- ZATCA (هيئة الزكاة والضريبة والجمارك): VAT registration\n"
            "- Sector-specific authorities: SFDA, MOH, REGA, CITC, MOE, RFTA\n\n"
            "For every license you report:\n"
            "- Provide the Arabic name (name_ar) and English name (name_en).\n"
            "- State the issuing authority.\n"
            "- Give the cost in SAR and processing timeline in business days.\n"
            "- Indicate whether it is mandatory (required) and available online.\n"
            "- Calculate total licensing cost and critical-path timeline.\n\n"
            "Return a JSON object with: sector, ownership_type, licenses (list), "
            "total_cost_sar, critical_path_days, sequential_days."
        )

    @property
    def tools(self) -> list:
        return [
            {
                "name": "lookup_mci_licenses",
                "description": (
                    "Returns all MCI-required licenses and registrations for a given sector, "
                    "including Commercial Registration, sector-specific permits, costs, "
                    "timelines, and issuing authorities."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sector": {
                            "type": "string",
                            "description": "Business sector (e.g. retail, food_beverage, healthcare, technology, franchise, real_estate)",
                        },
                    },
                    "required": ["sector"],
                },
            },
        ]

    def execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        if tool_name == "lookup_mci_licenses":
            return self._lookup_mci_licenses(**tool_input)
        raise NotImplementedError(f"Unknown tool: {tool_name}")

    def _lookup_mci_licenses(self, sector: str) -> dict:
        norm = normalize_sector(sector)
        licenses = get_licenses(norm)

        if not licenses:
            # Fallback: return a minimal default set
            licenses = [
                {
                    "name_ar": "السجل التجاري",
                    "name_en": "Commercial Registration (CR)",
                    "authority": "MCI (وزارة التجارة)",
                    "cost_sar": 1_200,
                    "timeline_days": 3,
                    "required": True,
                    "online": True,
                },
                {
                    "name_ar": "رخصة بلدية",
                    "name_en": "Municipality License",
                    "authority": "Balady (بلدي)",
                    "cost_sar": 2_500,
                    "timeline_days": 14,
                    "required": True,
                    "online": True,
                },
                {
                    "name_ar": "تسجيل ضريبة القيمة المضافة",
                    "name_en": "VAT Registration",
                    "authority": "ZATCA (هيئة الزكاة والضريبة والجمارك)",
                    "cost_sar": 0,
                    "timeline_days": 7,
                    "required": True,
                    "online": True,
                },
            ]

        total_cost = sum(lic.get("cost_sar", 0) for lic in licenses)
        timelines = [lic.get("timeline_days", 0) for lic in licenses]
        max_days = max(timelines) if timelines else 0
        seq_days = sum(timelines)

        return {
            "sector": sector,
            "licenses": licenses,
            "total_cost_sar": total_cost,
            "critical_path_days": max_days,
            "sequential_days": seq_days,
        }

    def _build_user_message(self, context: dict) -> str:
        sector = context.get("sector", "default")
        return (
            f"Look up all required Saudi commercial licenses for this business.\n"
            f"Sector: {sector}\n\n"
            f"Call lookup_mci_licenses with sector '{sector}'.\n"
            f"Return JSON with: sector, licenses, total_cost_sar, "
            f"critical_path_days, sequential_days."
        )
