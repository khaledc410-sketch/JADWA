"""
VisionOrchestrator — runs PillarAlignment, IncentivePrograms, and GigaProjects
sub-agents in parallel, then synthesizes with a reviewer pass.

Keeps name = "Vision2030Agent" so the pipeline layer remains unchanged.
"""

import json
from typing import Optional

from app.agents.base_agent import BaseAgent, SubAgentOrchestrator
from app.agents.vision.pillar_alignment_sub import PillarAlignmentSubAgent
from app.agents.vision.incentive_programs_sub import IncentiveProgramsSubAgent
from app.agents.vision.giga_projects_sub import GigaProjectsSubAgent


class VisionOrchestrator(SubAgentOrchestrator):
    name: str = "Vision2030Agent"
    description: str = (
        "Orchestrates Vision 2030 alignment scoring, government incentive mapping, "
        "and giga-project evaluation through parallel sub-agents"
    )
    temperature: float = 0.3
    reviewer_temperature: float = 0.2

    def get_sub_agents(self, context: dict) -> list:
        return [
            PillarAlignmentSubAgent(db=self.db, run_id=self.run_id),
            IncentiveProgramsSubAgent(db=self.db, run_id=self.run_id),
            GigaProjectsSubAgent(db=self.db, run_id=self.run_id),
        ]

    @property
    def reviewer_system_prompt(self) -> str:
        return (
            "أنت مستشار استراتيجي أول متخصص في رؤية السعودية 2030 ومحفزات الاستثمار.\n\n"
            "You are a senior Vision 2030 strategy consultant. Your role is to:\n"
            "- Synthesize pillar alignment analysis, incentive program matches, and "
            "giga-project opportunities into a single cohesive assessment.\n"
            "- Score overall Vision 2030 alignment (0-100) considering all sub-agent outputs.\n"
            "- Prioritize incentive programs by potential impact and ease of access.\n"
            "- Highlight the top 3 most impactful opportunities for the business.\n"
            "- Flag any conflicts or gaps between sub-agent outputs.\n"
            "- Provide bilingual (Arabic and English) executive summary.\n\n"
            "Return a JSON object with:\n"
            "- alignment_score (int 0-100)\n"
            "- aligned_pillars (list)\n"
            "- applicable_programs (list, ranked by impact)\n"
            "- giga_project_opportunities (list)\n"
            "- sez_benefits (list)\n"
            "- top_3_opportunities (list of concise recommendations)\n"
            "- narrative_ar (Arabic executive summary)\n"
            "- narrative_en (English executive summary)\n\n"
            "No text outside the JSON block."
        )

    def _build_user_message(self, context: dict) -> str:
        sector = context.get("sector", "default")
        is_saudi = context.get("investor_nationality", "SA") == "SA"
        investment = context.get("investment_amount_sar", 1_000_000)
        return (
            f"Evaluate Vision 2030 alignment and incentives for this Saudi business.\n"
            f"Sector: {sector} | Saudi-owned: {is_saudi} | Investment: SAR {investment:,.0f}\n\n"
            f"Steps:\n"
            f"1. Call evaluate_vision_alignment for sector '{sector}'.\n"
            f"2. Call lookup_incentive_programs for '{sector}'.\n"
            f"3. Call fetch_giga_projects and fetch_sez_benefits.\n\n"
            f"Return JSON: alignment_score, aligned_pillars, applicable_programs, "
            f"giga_project_opportunities, sez_benefits, narrative_ar, narrative_en.\n\n"
            f"Full context:\n{json.dumps(context, ensure_ascii=False, indent=2)}"
        )
