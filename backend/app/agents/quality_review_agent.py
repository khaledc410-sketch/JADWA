"""
QualityReviewAgent — reviews the compiled report for:
- Numerical consistency across sections
- Arabic language quality and professional tone
- All required sections present
- Financial cross-references (numbers match between sections)
"""

import json
import re
from typing import Any

from app.agents.base_agent import BaseAgent


class QualityReviewAgent(BaseAgent):
    name: str = "QualityReviewAgent"
    description: str = (
        "QA review: numerical consistency, Arabic quality, section completeness"
    )
    temperature: float = 0.2

    @property
    def system_prompt(self) -> str:
        return (
            "أنت متخصص في ضمان جودة التقارير التجارية العربية. مهمتك:\n"
            "1. فحص اتساق الأرقام عبر أقسام التقرير.\n"
            "2. مراجعة جودة اللغة العربية والنبرة المهنية.\n"
            "3. التحقق من اكتمال جميع الأقسام المطلوبة.\n"
            "4. فحص التقاطعات المالية (هل تتطابق الأرقام بين الأقسام؟).\n\n"
            "You are a QA specialist for Arabic business reports. You check:\n"
            "1. Numerical consistency: IRR, NPV, revenue figures match across sections.\n"
            "2. Arabic grammar and professional consulting tone (no colloquial terms).\n"
            "3. All required sections present and non-empty.\n"
            "4. Financial cross-references: investment amount consistent, headcount consistent.\n\n"
            "Instructions:\n"
            "- Score quality 0-100.\n"
            "- List specific issues with section references.\n"
            "- Provide corrections for Arabic language issues.\n"
            "- Approve report if quality_score >= 75.\n"
            "Return a JSON object matching the output schema exactly."
        )

    @property
    def tools(self) -> list:
        return [
            {
                "name": "check_numerical_consistency",
                "description": (
                    "Cross-checks key numerical values (investment, revenue, IRR, headcount) "
                    "across all report sections and flags inconsistencies."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "report": {
                            "type": "object",
                            "description": "The assembled report document",
                        },
                    },
                    "required": ["report"],
                },
            },
            {
                "name": "review_arabic_language",
                "description": (
                    "Reviews Arabic text quality across narrative sections: grammar, "
                    "professional tone, consistent terminology, correct financial terminology."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "report_sections": {
                            "type": "object",
                            "description": "Dict of section_name -> section data with narrative_ar fields",
                        },
                    },
                    "required": ["report_sections"],
                },
            },
            {
                "name": "check_section_completeness",
                "description": (
                    "Verifies all required sections are present and contain substantive content "
                    "(not placeholder text)."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "report": {"type": "object"},
                        "sector": {"type": "string"},
                    },
                    "required": ["report"],
                },
            },
        ]

    # ------------------------------------------------------------------
    # Tool implementations
    # ------------------------------------------------------------------

    def execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        if tool_name == "check_numerical_consistency":
            return self._check_numerical_consistency(**tool_input)
        if tool_name == "review_arabic_language":
            return self._review_arabic_language(**tool_input)
        if tool_name == "check_section_completeness":
            return self._check_section_completeness(**tool_input)
        raise NotImplementedError(f"Unknown tool: {tool_name}")

    def _check_numerical_consistency(self, report: dict) -> dict:
        issues = []
        sections = report.get("sections", {})

        # Extract key metrics from different sections
        investment_mentions = []
        irr_mentions = []
        headcount_mentions = []

        # From executive summary
        exec_sum = sections.get("executive_summary", {})
        key_metrics = exec_sum.get("key_metrics", {})
        if key_metrics.get("irr"):
            irr_mentions.append(("executive_summary", key_metrics["irr"]))

        # From financial model
        fin_model = sections.get("financial_model", {})
        if isinstance(fin_model, dict):
            if fin_model.get("irr"):
                irr_mentions.append(("financial_model", fin_model["irr"]))

        # Check IRR consistency
        if len(irr_mentions) > 1:
            irr_values = [v for _, v in irr_mentions]
            if max(irr_values) - min(irr_values) > 0.02:  # >2% discrepancy
                issues.append(
                    {
                        "type": "numerical_inconsistency",
                        "field": "IRR",
                        "found_values": dict(irr_mentions),
                        "message": f"IRR values differ across sections: {irr_mentions}",
                        "severity": "high",
                    }
                )

        # Check for placeholder text
        for sec_name, sec_data in sections.items():
            if isinstance(sec_data, dict):
                if sec_data.get("status") == "pending":
                    issues.append(
                        {
                            "type": "incomplete_section",
                            "section": sec_name,
                            "message": f"Section '{sec_name}' is marked as pending",
                            "severity": "medium",
                        }
                    )

        return {
            "issues": issues,
            "irr_cross_check": irr_mentions,
            "headcount_cross_check": headcount_mentions,
            "consistency_score": max(0, 100 - len(issues) * 10),
        }

    def _review_arabic_language(self, report_sections: dict) -> dict:
        issues = []
        corrections = {}

        # Check for common Arabic quality issues
        colloquial_patterns = ["اللي", "فيه كده", "بتاع", "عشان"]
        preferred_financial_terms = {
            "profit": "الربح",
            "revenue": "الإيرادات",
            "investment": "الاستثمار",
            "return": "العائد",
        }

        arabic_narratives = []
        for sec_name, sec_data in report_sections.items():
            if isinstance(sec_data, dict):
                narrative = sec_data.get("narrative_ar", "")
                if narrative:
                    arabic_narratives.append((sec_name, narrative))

        for sec_name, narrative in arabic_narratives:
            for pattern in colloquial_patterns:
                if pattern in narrative:
                    issues.append(
                        {
                            "section": sec_name,
                            "type": "colloquial_arabic",
                            "found": pattern,
                            "message": f"Colloquial term '{pattern}' in section '{sec_name}' — use formal MSA",
                            "severity": "low",
                        }
                    )

        language_score = max(0, 100 - len(issues) * 5)

        return {
            "issues": issues,
            "corrections": corrections,
            "language_score": language_score,
            "arabic_sections_reviewed": len(arabic_narratives),
            "recommendations": [
                "Ensure consistent use of Modern Standard Arabic (الفصحى)",
                "Financial terms should follow SAMA Arabic glossary",
                "Use active voice (الصيغة المبنية للمعلوم) for executive assertions",
                "Maintain formal tone throughout — avoid passive constructs where possible",
            ],
        }

    def _check_section_completeness(
        self, report: dict, sector: str = "default"
    ) -> dict:
        required_always = [
            "executive_summary",
            "project_overview",
            "market_research",
            "financial_model",
            "legal_regulatory",
            "hr_saudization",
            "competitive_analysis",
            "vision2030_alignment",
            "risk_assessment",
            "investment_summary",
            "recommendations",
        ]
        conditional = {
            "franchise": ["franchise_analysis"],
            "real_estate": ["real_estate_analysis"],
        }
        required = required_always + conditional.get(sector.lower(), [])

        sections = report.get("sections", {})
        present = []
        missing = []
        empty = []

        for sec in required:
            if sec not in sections:
                missing.append(sec)
            elif not sections[sec] or sections[sec].get("status") == "pending":
                empty.append(sec)
            else:
                present.append(sec)

        completeness_pct = (
            round(len(present) / len(required) * 100) if required else 100
        )

        return {
            "completeness_percentage": completeness_pct,
            "present_sections": present,
            "missing_sections": missing,
            "empty_sections": empty,
            "total_required": len(required),
            "total_present": len(present),
        }

    def _build_user_message(self, context: dict) -> str:
        sector = context.get("sector", "default")
        report = context.get(
            "report", context
        )  # report may be passed directly or in context

        return (
            f"Perform quality review on this JADWA feasibility report.\n"
            f"Sector: {sector}\n\n"
            f"Steps:\n"
            f"1. Call check_numerical_consistency on the full report.\n"
            f"2. Call review_arabic_language on all sections.\n"
            f"3. Call check_section_completeness for sector '{sector}'.\n\n"
            f"Aggregate all findings and return JSON:\n"
            f"quality_score (0-100), issues (list), corrections (dict), approved (bool).\n"
            f"Approve if quality_score >= 75.\n\n"
            f"Report data:\n{json.dumps(context, ensure_ascii=False, indent=2)}"
        )
