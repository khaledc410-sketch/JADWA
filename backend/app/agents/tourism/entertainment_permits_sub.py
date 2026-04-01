"""
EntertainmentPermitsSubAgent — checks GEA (General Entertainment Authority)
permit types and entertainment venue requirements for Saudi Arabia.
"""

from typing import Any

from app.agents.base_agent import BaseAgent
from app.services.data_tools import get_entertainment_permits


class EntertainmentPermitsSubAgent(BaseAgent):
    name: str = "EntertainmentPermitsSubAgent"
    description: str = "GEA entertainment permits and venue requirements"
    max_tokens: int = 2000
    temperature: float = 0.1

    @property
    def system_prompt(self) -> str:
        return (
            "أنت متخصص في تصاريح الهيئة العامة للترفيه (GEA) في المملكة العربية السعودية.\n\n"
            "You are a GEA (General Entertainment Authority) permits specialist.\n\n"
            "Your responsibilities:\n"
            "- Check GEA permit types for entertainment events and venues.\n"
            "- Identify required permits based on event type and scale.\n"
            "- Provide entertainment venue requirements and compliance rules.\n"
            "- Flag any compliance risks or regulatory concerns.\n"
            "- All monetary values in SAR.\n"
            "- Return a JSON object with: entertainment_permits, venue_requirements.\n"
            "  No text outside the JSON block."
        )

    @property
    def tools(self) -> list:
        return [
            {
                "name": "check_gea_permits",
                "description": (
                    "Checks GEA entertainment permit types. Optionally filters by "
                    "event_type keyword (e.g. 'concert', 'festival', 'theme_park', 'cinema')."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "event_type": {
                            "type": "string",
                            "description": (
                                "Event type keyword to filter permits "
                                "(e.g. 'concert', 'festival', 'theme_park', 'cinema')"
                            ),
                        },
                    },
                    "required": [],
                },
            },
            {
                "name": "get_entertainment_requirements",
                "description": (
                    "Returns general entertainment venue and event requirements "
                    "including safety standards, capacity limits, and operational rules."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        ]

    def execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        if tool_name == "check_gea_permits":
            return self._check_gea_permits(tool_input)
        if tool_name == "get_entertainment_requirements":
            return self._get_entertainment_requirements()
        raise NotImplementedError(f"Unknown tool: {tool_name}")

    def _check_gea_permits(self, tool_input: dict) -> list:
        event_type = tool_input.get("event_type", "")
        all_permits = get_entertainment_permits()
        if not event_type:
            return all_permits
        keyword = event_type.lower()
        filtered = [
            p
            for p in all_permits
            if keyword in str(p.get("type", "")).lower()
            or keyword in str(p.get("name", "")).lower()
            or keyword in str(p.get("event_type", "")).lower()
            or keyword in str(p.get("category", "")).lower()
            or keyword in str(p.get("description", "")).lower()
        ]
        return filtered if filtered else all_permits

    def _get_entertainment_requirements(self) -> list:
        return get_entertainment_permits()
