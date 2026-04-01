"""
STALicensingSubAgent — looks up Saudi Tourism Authority license types
and hotel classification standards.
"""

from typing import Any

from app.agents.base_agent import BaseAgent
from app.services.data_tools import get_sta_licenses, get_hotel_classification


class STALicensingSubAgent(BaseAgent):
    name: str = "STALicensingSubAgent"
    description: str = "STA licensing and hotel classification lookup"
    max_tokens: int = 2000
    temperature: float = 0.1

    @property
    def system_prompt(self) -> str:
        return (
            "أنت متخصص في تراخيص الهيئة السعودية للسياحة (STA).\n\n"
            "You are a Saudi Tourism Authority (STA) licensing specialist.\n\n"
            "Your responsibilities:\n"
            "- Look up STA license types required for tourism and hospitality businesses.\n"
            "- Check hotel classification standards and star-rating requirements.\n"
            "- Identify applicable license categories based on the business activity.\n"
            "- Flag any compliance risks or missing licenses.\n"
            "- All monetary values in SAR.\n"
            "- Return a JSON object with: sta_licenses, hotel_classification.\n"
            "  No text outside the JSON block."
        )

    @property
    def tools(self) -> list:
        return [
            {
                "name": "lookup_sta_license",
                "description": (
                    "Looks up STA tourism license types. Optionally filters by "
                    "license_type keyword (e.g. 'hotel', 'travel_agency', 'tour_guide')."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "license_type": {
                            "type": "string",
                            "description": (
                                "License type keyword to filter results "
                                "(e.g. 'hotel', 'travel_agency', 'tour_guide')"
                            ),
                        },
                    },
                    "required": [],
                },
            },
            {
                "name": "get_hotel_classification_data",
                "description": (
                    "Returns hotel classification standards and requirements. "
                    "Optionally filters by star_rating (1-5)."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "star_rating": {
                            "type": "integer",
                            "description": "Star rating to filter (1-5)",
                        },
                    },
                    "required": [],
                },
            },
        ]

    def execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        if tool_name == "lookup_sta_license":
            return self._lookup_sta_license(tool_input)
        if tool_name == "get_hotel_classification_data":
            return self._get_hotel_classification_data(tool_input)
        raise NotImplementedError(f"Unknown tool: {tool_name}")

    def _lookup_sta_license(self, tool_input: dict) -> list:
        license_type = tool_input.get("license_type", "")
        all_licenses = get_sta_licenses()
        if not license_type:
            return all_licenses
        keyword = license_type.lower()
        filtered = [
            lic
            for lic in all_licenses
            if keyword in str(lic.get("type", "")).lower()
            or keyword in str(lic.get("name", "")).lower()
            or keyword in str(lic.get("category", "")).lower()
            or keyword in str(lic.get("description", "")).lower()
        ]
        return filtered if filtered else all_licenses

    def _get_hotel_classification_data(self, tool_input: dict) -> list:
        star_rating = tool_input.get("star_rating", 0)
        all_classifications = get_hotel_classification()
        if not star_rating:
            return all_classifications
        filtered = [
            c
            for c in all_classifications
            if c.get("star_rating") == star_rating
            or c.get("stars") == star_rating
            or c.get("rating") == star_rating
        ]
        return filtered if filtered else all_classifications
