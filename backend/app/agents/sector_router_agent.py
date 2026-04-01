"""
SectorRouterAgent — determines which specialized agents to activate
based on the validated business sector and project characteristics.
Pure logic: no external tools, no Claude API needed beyond routing.
"""

import json
from typing import Any

from app.agents.base_agent import BaseAgent


# Canonical pipeline per sector  (always-on agents are added first)
ALWAYS_ON_AGENTS = [
    "market_research",
    "financial_modeling",
    "legal_regulatory",
    "hr_saudization",
    "competitive_analysis",
    "vision2030",
    "risk_assessment",
    "chart_generation",
    "report_compiler",
    "quality_review",
    "pdf_render",
]

SECTOR_EXTRA_AGENTS = {
    "franchise": ["franchise"],
    "real_estate": ["real_estate"],
    "healthcare": ["healthcare"],
    "education": ["education"],
    "technology": ["tech"],
    "hospitality": ["tourism"],
    "manufacturing": ["manufacturing"],
    "logistics": ["logistics"],
}

REPORT_TEMPLATES = {
    "franchise": "franchise",
    "real_estate": "real_estate",
    "healthcare": "regulated_sector",
    "food_beverage": "restaurant_cafe",
    "technology": "tech_startup",
    "manufacturing": "industrial",
    "education": "regulated_sector",
    "hospitality": "hospitality",
    "logistics": "logistics",
    "retail": "standard_sme",
    "default": "standard_sme",
}

SECTOR_CONFIGS = {
    "retail": {
        "nitaqat_min_percentage": 25,
        "vat_applicable": True,
        "municipality_license": True,
        "avg_lease_sqm_sar": 1_800,
        "key_regulator": "MCI",
    },
    "food_beverage": {
        "nitaqat_min_percentage": 20,
        "vat_applicable": True,
        "municipality_license": True,
        "sfda_required": True,
        "avg_lease_sqm_sar": 2_200,
        "key_regulator": "SFDA",
    },
    "healthcare": {
        "nitaqat_min_percentage": 35,
        "vat_applicable": False,
        "moh_license": True,
        "avg_lease_sqm_sar": 2_500,
        "key_regulator": "MOH",
    },
    "education": {
        "nitaqat_min_percentage": 30,
        "vat_applicable": False,
        "moe_license": True,
        "avg_lease_sqm_sar": 1_600,
        "key_regulator": "MOE",
    },
    "technology": {
        "nitaqat_min_percentage": 25,
        "vat_applicable": True,
        "municipality_license": False,
        "avg_lease_sqm_sar": 1_400,
        "key_regulator": "CITC",
    },
    "real_estate": {
        "nitaqat_min_percentage": 35,
        "vat_applicable": True,
        "rega_license": True,
        "avg_construction_sqm_sar": 2_800,
        "key_regulator": "REGA",
    },
    "franchise": {
        "nitaqat_min_percentage": 25,
        "vat_applicable": True,
        "rfta_registration": True,
        "avg_franchise_fee_sar": 150_000,
        "key_regulator": "RFTA",
    },
    "manufacturing": {
        "nitaqat_min_percentage": 30,
        "vat_applicable": True,
        "sec_license": True,
        "modon_zone": True,
        "key_regulator": "Ministry of Industry",
    },
    "logistics": {
        "nitaqat_min_percentage": 35,
        "vat_applicable": True,
        "mot_license": True,
        "key_regulator": "MOT",
    },
    "hospitality": {
        "nitaqat_min_percentage": 35,
        "vat_applicable": True,
        "tourism_license": True,
        "key_regulator": "MOMRA / Tourism",
    },
    "default": {
        "nitaqat_min_percentage": 25,
        "vat_applicable": True,
        "municipality_license": True,
        "key_regulator": "MCI",
    },
}


class SectorRouterAgent(BaseAgent):
    name: str = "SectorRouterAgent"
    description: str = "Routes pipeline to appropriate sector-specific agents"

    @property
    def system_prompt(self) -> str:
        return (
            "You are the pipeline orchestrator for the JADWA Saudi feasibility study "
            "platform. Given a validated business context, determine:\n"
            "1. Which specialized agents must be activated (agent_dag).\n"
            "2. Which report template to use.\n"
            "3. The sector-specific configuration object.\n\n"
            "Return a valid JSON object with keys: agent_dag, report_template, sector_config.\n"
            "Do NOT add commentary outside the JSON block."
        )

    @property
    def tools(self) -> list:
        # No external tools needed — pure routing logic
        return []

    def execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        raise NotImplementedError(
            f"SectorRouterAgent has no tools (received: {tool_name})"
        )

    # ------------------------------------------------------------------
    # Override run() — pure Python routing, no Claude call needed
    # ------------------------------------------------------------------

    def run(self, context: dict) -> dict:
        from datetime import datetime

        self.started_at = datetime.utcnow()
        sector = (
            context.get("sector")
            or context.get("validated_context", {}).get("sector", "default")
        ).lower()

        agent_dag = list(ALWAYS_ON_AGENTS)  # copy
        extra = SECTOR_EXTRA_AGENTS.get(sector, [])
        # Insert sector-specific agents right after hr_saudization
        insert_at = agent_dag.index("competitive_analysis")
        for agent in reversed(extra):
            agent_dag.insert(insert_at, agent)

        report_template = REPORT_TEMPLATES.get(sector, REPORT_TEMPLATES["default"])
        sector_config = SECTOR_CONFIGS.get(sector, SECTOR_CONFIGS["default"])

        result = {
            "agent_dag": agent_dag,
            "report_template": report_template,
            "sector_config": sector_config,
            "sector": sector,
            "agent": self.name,
        }

        self.completed_at = datetime.utcnow()
        self._log_to_db(context, result, status="completed")
        return result

    def _build_user_message(self, context: dict) -> str:
        return (
            "Determine the agent pipeline and sector configuration for this project.\n\n"
            f"Validated Context:\n{json.dumps(context, ensure_ascii=False, indent=2)}"
        )
