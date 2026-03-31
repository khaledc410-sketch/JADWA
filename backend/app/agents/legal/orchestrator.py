"""
LegalOrchestrator — runs Licensing, ForeignOwnership, and SMEPrograms
sub-agents in parallel, then synthesizes a complete legal roadmap.
"""

import json
from typing import Optional

from app.agents.base_agent import SubAgentOrchestrator
from app.agents.legal.licensing_sub import LicensingSubAgent
from app.agents.legal.foreign_ownership_sub import ForeignOwnershipSubAgent
from app.agents.legal.sme_programs_sub import SMEProgramsSubAgent


class LegalOrchestrator(SubAgentOrchestrator):
    name: str = "LegalRegulatoryAgent"
    description: str = (
        "Saudi licenses, permits, regulatory requirements with costs and timelines"
    )
    temperature: float = 0.2

    @property
    def reviewer_system_prompt(self) -> str:
        return (
            "أنت مستشار تنظيمي سعودي أول تقوم بإعداد خارطة طريق قانونية شاملة لتأسيس الأعمال.\n\n"
            "You are a senior Saudi regulatory advisor compiling a complete legal roadmap.\n\n"
            "You have received outputs from three specialist sub-agents:\n"
            "1. LicensingSubAgent — MCI licenses, costs, timelines\n"
            "2. ForeignOwnershipSubAgent — MISA rules, capital requirements, negative list\n"
            "3. SMEProgramsSubAgent — Monsha'at programs, sector regulators\n\n"
            "Your task:\n"
            "- Cross-validate data across sub-agents (e.g. license costs should be consistent).\n"
            "- Resolve any conflicts by choosing the most authoritative source.\n"
            "- Build a single sequenced licensing timeline (critical path).\n"
            "- Calculate grand total of all licensing and registration costs in SAR.\n"
            "- Flag compliance risks for the investor profile.\n"
            "- Provide bilingual narrative summaries (Arabic and English).\n\n"
            "Return a JSON object with:\n"
            "- licenses: complete list with costs and timelines\n"
            "- total_licensing_cost_sar: grand total\n"
            "- total_timeline_days: critical-path estimate\n"
            "- foreign_ownership: MISA requirements summary\n"
            "- sme_programs: eligible programs\n"
            "- sector_regulator: primary regulator details\n"
            "- compliance_flags: list of risk items\n"
            "- narrative_ar: Arabic summary\n"
            "- narrative_en: English summary\n\n"
            "No text outside the JSON block."
        )

    def get_sub_agents(self, context: dict) -> list:
        return [
            LicensingSubAgent(db=self.db, run_id=self.run_id),
            ForeignOwnershipSubAgent(db=self.db, run_id=self.run_id),
            SMEProgramsSubAgent(db=self.db, run_id=self.run_id),
        ]

    def _build_user_message(self, context: dict) -> str:
        sector = context.get("sector", "default")
        city = context.get("city", "Riyadh")
        nationality = context.get("investor_nationality", "SA")
        return (
            f"Compile a complete Saudi legal and regulatory roadmap for this business.\n"
            f"Sector: {sector} | City: {city} | Investor nationality: {nationality}\n\n"
            f"Sub-agent outputs are provided below. Synthesize them into a single "
            f"cohesive legal roadmap with total costs, critical-path timeline, "
            f"and compliance flags.\n\n"
            f"Full context:\n{json.dumps(context, ensure_ascii=False, indent=2)}"
        )
