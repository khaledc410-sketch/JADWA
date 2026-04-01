"""
LogisticsLicensingSubAgent — looks up MOT transport licenses and logistics
hub data for Saudi logistics company feasibility assessments.
"""

from typing import Any

from app.agents.base_agent import BaseAgent
from app.services.data_tools import get_transport_licenses, get_logistics_hubs


class LogisticsLicensingSubAgent(BaseAgent):
    name: str = "LogisticsLicensingSubAgent"
    description: str = "Saudi MOT transport licensing and logistics hub specialist"
    max_tokens: int = 2000
    temperature: float = 0.2

    @property
    def system_prompt(self) -> str:
        return (
            "أنت متخصص في تراخيص النقل وزارة النقل والخدمات اللوجستية السعودية.\n\n"
            "You are a Saudi MOT (Ministry of Transport) licensing specialist "
            "for logistics companies.\n\n"
            "Your expertise:\n"
            "- Transport license categories: freight, passenger, last-mile, cold chain.\n"
            "- MOT regulatory requirements and compliance procedures.\n"
            "- Fleet registration, driver licensing, and GPS tracking mandates.\n"
            "- Logistics hub zones: dry ports, distribution centers, intermodal facilities.\n"
            "- SAR-denominated fee schedules and annual renewal costs.\n\n"
            "Instructions:\n"
            "- Match license types to the correct MOT category.\n"
            "- Identify all required permits and fleet compliance steps.\n"
            "- Recommend optimal logistics hub based on region and operations.\n"
            "- All monetary values in SAR.\n"
            "- Return a JSON object with: license_details, compliance_requirements, "
            "hub_recommendation.\n"
            "  No text outside the JSON block."
        )

    @property
    def tools(self) -> list:
        return [
            {
                "name": "lookup_transport_license",
                "description": (
                    "Looks up MOT transport license requirements for a given license type. "
                    "Returns license category, fees, required documents, and processing time."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "license_type": {
                            "type": "string",
                            "description": "Type of transport license (e.g. freight, passenger, last_mile, cold_chain)",
                        },
                    },
                    "required": ["license_type"],
                },
            },
            {
                "name": "get_logistics_hubs_data",
                "description": (
                    "Retrieves logistics hub data for a given region. Returns hub locations, "
                    "capacity, connectivity (ports, airports, rail), and lease costs."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "region": {
                            "type": "string",
                            "description": "Target region (e.g. Riyadh, Jeddah, Dammam, Eastern Province)",
                        },
                    },
                    "required": ["region"],
                },
            },
        ]

    def execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        if tool_name == "lookup_transport_license":
            return self._lookup_transport_license(tool_input)
        if tool_name == "get_logistics_hubs_data":
            return self._get_logistics_hubs_data(tool_input)
        raise NotImplementedError(f"Unknown tool: {tool_name}")

    # ── Tool implementations ──────────────────────────────────────────────

    def _lookup_transport_license(self, tool_input: dict) -> dict:
        license_type = tool_input.get("license_type", "freight")
        licenses = get_transport_licenses()
        type_lower = license_type.lower().strip()

        matching = [
            lic
            for lic in licenses
            if type_lower in lic.get("license_type", "").lower()
            or type_lower in lic.get("category", "").lower()
            or type_lower in lic.get("name", "").lower()
        ]

        if not matching:
            return {
                "license_type": license_type,
                "status": "not_found",
                "message": (
                    f"No specific license category found for '{license_type}'. "
                    "A general transport license (MOT) may apply."
                ),
                "all_categories": [
                    lic.get("license_type", lic.get("name", ""))
                    for lic in licenses[:10]
                ],
            }

        return {
            "license_type": license_type,
            "status": "found",
            "matching_licenses": matching,
            "total_matches": len(matching),
        }

    def _get_logistics_hubs_data(self, tool_input: dict) -> dict:
        region = tool_input.get("region", "Riyadh")
        hubs = get_logistics_hubs()
        region_lower = region.lower().strip()

        matching = [
            h
            for h in hubs
            if region_lower in h.get("region", "").lower()
            or region_lower in h.get("city", "").lower()
            or region_lower in h.get("name", "").lower()
        ]

        if not matching:
            matching = hubs  # return all as alternatives

        return {
            "search_region": region,
            "matching_hubs": matching,
            "total_found": len(matching),
            "note": (
                "Consider proximity to ports, airports, and rail networks "
                "when selecting a logistics hub."
            ),
        }
