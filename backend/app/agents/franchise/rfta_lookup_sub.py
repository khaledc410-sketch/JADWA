"""
RFTALookupSubAgent — matches franchise brands against the RFTA registry (847 entries).
Returns registration status, fee structures, royalties, and territory data.
"""

from typing import Any

from app.agents.base_agent import BaseAgent
from app.services.data_tools import lookup_franchise, search_franchises


class RFTALookupSubAgent(BaseAgent):
    name: str = "RFTALookupSubAgent"
    description: str = "Matches franchise brands against the RFTA registry"
    max_tokens: int = 4096
    temperature: float = 0.1

    @property
    def system_prompt(self) -> str:
        return (
            "أنت متخصص في سجل الامتياز التجاري السعودي (RFTA) وقاعدة بيانات العلامات التجارية المسجلة.\n\n"
            "You are an RFTA (Saudi Franchise Registry) specialist with access to the full "
            "registry of 847 registered franchise brands.\n\n"
            "Your responsibilities:\n"
            "- Look up franchise brands by name (English or Arabic) and return their RFTA "
            "  registration details: status, fees, royalties, territory rights.\n"
            "- Search the franchise database by sector or keyword to find matching brands.\n"
            "- Flag unregistered or expired franchise registrations.\n"
            "- All monetary values in SAR.\n"
            "- Return a JSON object with: rfta_registration, fee_structure, territory_data.\n"
            "  No text outside the JSON block."
        )

    @property
    def tools(self) -> list:
        return [
            {
                "name": "lookup_rfta_franchise",
                "description": (
                    "Looks up a franchise brand in the RFTA registry by name (English or Arabic). "
                    "Returns registration status, fee structure, royalties, and territory data."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "brand_name": {
                            "type": "string",
                            "description": "Franchise brand name in English or Arabic",
                        },
                    },
                    "required": ["brand_name"],
                },
            },
            {
                "name": "search_franchise_database",
                "description": (
                    "Searches the RFTA franchise database by sector and/or keyword query. "
                    "Returns a list of matching franchise entries."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sector": {
                            "type": "string",
                            "description": "Sector filter (e.g. food_beverage, retail, healthcare)",
                        },
                        "query": {
                            "type": "string",
                            "description": "Free-text search query to match against franchise names",
                        },
                    },
                    "required": [],
                },
            },
        ]

    def execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        if tool_name == "lookup_rfta_franchise":
            return self._lookup_rfta_franchise(**tool_input)
        if tool_name == "search_franchise_database":
            return self._search_franchise_database(**tool_input)
        raise NotImplementedError(f"Unknown tool: {tool_name}")

    def _lookup_rfta_franchise(self, brand_name: str) -> dict:
        result = lookup_franchise(brand_name)
        if result is None:
            return {
                "brand_name": brand_name,
                "rfta_status": "not_found",
                "message": (
                    f"Brand '{brand_name}' was not found in the RFTA registry. "
                    "The franchisor may not be registered in Saudi Arabia."
                ),
            }
        return result

    def _search_franchise_database(self, sector: str = None, query: str = None) -> list:
        return search_franchises(sector=sector, query=query)
