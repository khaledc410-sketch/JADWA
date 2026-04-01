"""
ReportCompilerAgent — assembles all agent outputs into a final structured
ReportDocument JSON with all 16 sections and an executive summary.
"""

import json
from datetime import datetime
from typing import Any

from app.agents.base_agent import BaseAgent

# Section identifiers used in the final report structure
REPORT_SECTIONS = [
    "executive_summary",
    "project_overview",
    "market_research",
    "financial_model",
    "legal_regulatory",
    "hr_saudization",
    "competitive_analysis",
    "vision2030_alignment",
    "risk_assessment",
    "franchise_analysis",  # conditional — present only for franchise sector
    "real_estate_analysis",  # conditional — present only for real_estate sector
    "investment_summary",
    "charts",
    "recommendations",
    "glossary",
    "appendix",
]


class ReportCompilerAgent(BaseAgent):
    name: str = "ReportCompilerAgent"
    description: str = "Assembles all agent outputs into the final ReportDocument JSON"
    max_tokens: int = 8192
    temperature: float = 0.4

    @property
    def system_prompt(self) -> str:
        return (
            "أنت مستشار أعمال أول وكاتب تقارير متخصص في اللغتين العربية والإنجليزية.\n\n"
            "You are a senior business consultant and report writer expert in Arabic and English "
            "business writing. You assemble comprehensive feasibility reports that are:\n"
            "- Professional consulting quality (McKinsey / BCG tone)\n"
            "- Bilingual: Arabic as primary language, English as secondary\n"
            "- Data-driven with specific SAR figures and percentages\n"
            "- Actionable: each section ends with concrete recommendations\n\n"
            "Instructions:\n"
            "1. Use compile_executive_summary to write the executive summary.\n"
            "2. Use assemble_report_sections to structure all sections.\n"
            "3. Use validate_report_completeness to verify all required sections are present.\n"
            "4. Return the complete ReportDocument JSON.\n\n"
            "The executive summary must include:\n"
            "- Project name and sector\n"
            "- Investment amount in SAR\n"
            "- Key financial metrics (IRR, NPV, payback period)\n"
            "- Vision 2030 alignment score\n"
            "- Overall feasibility verdict: RECOMMENDED / CONDITIONAL / NOT RECOMMENDED\n"
            "- 3-5 key risks and mitigations\n"
            "- Top 3 action items\n\n"
            "Return the full ReportDocument dict as JSON. No text outside the JSON block."
        )

    @property
    def tools(self) -> list:
        return [
            {
                "name": "compile_executive_summary",
                "description": (
                    "Compiles a bilingual executive summary (Arabic primary, English secondary) "
                    "from all agent outputs. Includes feasibility verdict and top 3 recommendations."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "project_name": {"type": "string"},
                        "sector": {"type": "string"},
                        "investment_sar": {"type": "number"},
                        "irr": {"type": "number"},
                        "npv_sar": {"type": "number"},
                        "payback_months": {"type": "integer"},
                        "vision_score": {"type": "integer"},
                        "risk_rating": {"type": "string"},
                        "nitaqat_band": {"type": "string"},
                    },
                    "required": ["project_name", "sector"],
                },
            },
            {
                "name": "assemble_report_sections",
                "description": (
                    "Structures all agent outputs into the standard 16-section report format, "
                    "adding section headings, subsections, and cross-references."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sections_data": {
                            "type": "object",
                            "description": "Dict of section_name -> agent output data",
                        },
                        "report_template": {
                            "type": "string",
                            "description": "standard_sme | franchise | real_estate | regulated_sector",
                        },
                    },
                    "required": ["sections_data"],
                },
            },
            {
                "name": "validate_report_completeness",
                "description": (
                    "Validates that all required report sections are present and non-empty. "
                    "Returns completeness score and list of missing sections."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "report": {"type": "object"},
                        "required_sections": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                    "required": ["report"],
                },
            },
        ]

    # ------------------------------------------------------------------
    # Tool implementations
    # ------------------------------------------------------------------

    def execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        if tool_name == "compile_executive_summary":
            return self._compile_executive_summary(tool_input)
        if tool_name == "assemble_report_sections":
            return self._assemble_report_sections(tool_input)
        if tool_name == "validate_report_completeness":
            return self._validate_report_completeness(tool_input)
        raise NotImplementedError(f"Unknown tool: {tool_name}")

    def _compile_executive_summary(self, data: dict) -> dict:
        project_name = data.get("project_name", "")
        sector = data.get("sector", "")
        investment_sar = data.get("investment_sar", 0)
        irr = data.get("irr", 0)
        npv_sar = data.get("npv_sar", data.get("npv", 0))
        payback_months = data.get("payback_months", 0)
        vision_score = data.get("vision_score", 75)
        risk_rating = data.get("risk_rating", "medium")
        nitaqat_band = data.get("nitaqat_band", "low_green")
        # Determine feasibility verdict
        if irr > 0.20 and risk_rating in ["low", "medium"] and vision_score >= 70:
            verdict_en = "RECOMMENDED"
            verdict_ar = "موصى به"
            verdict_color = "green"
        elif irr > 0.12 or vision_score >= 60:
            verdict_en = "CONDITIONAL"
            verdict_ar = "مشروط"
            verdict_color = "yellow"
        else:
            verdict_en = "REQUIRES FURTHER STUDY"
            verdict_ar = "يتطلب مزيداً من الدراسة"
            verdict_color = "orange"

        return {
            "project_name": project_name,
            "sector": sector,
            "investment_sar": investment_sar,
            "report_date": datetime.utcnow().strftime("%Y-%m-%d"),
            "feasibility_verdict_en": verdict_en,
            "feasibility_verdict_ar": verdict_ar,
            "verdict_color": verdict_color,
            "key_metrics": {
                "irr": irr,
                "npv_sar": npv_sar,
                "payback_months": payback_months,
                "vision_alignment_score": vision_score,
                "risk_rating": risk_rating,
                "nitaqat_band": nitaqat_band,
            },
            "executive_summary_ar": (
                f"يُقدم هذا التقرير دراسة جدوى شاملة لمشروع {project_name} في قطاع "
                f"{sector} بالمملكة العربية السعودية. يبلغ إجمالي الاستثمار المطلوب "
                f"{investment_sar:,.0f} ريال سعودي، مع معدل عائد داخلي متوقع يبلغ "
                f"{irr * 100:.1f}٪ وصافي قيمة حالية قدره {npv_sar:,.0f} ريال. "
                f"يتوافق المشروع بنسبة {vision_score}٪ مع أهداف رؤية المملكة 2030، "
                f"ويحقق نطاقات بمستوى {nitaqat_band.replace('_', ' ').title()}. "
                f"الحكم العام: {verdict_ar}."
            ),
            "executive_summary_en": (
                f"This report presents a comprehensive feasibility study for {project_name} "
                f"in the {sector} sector in Saudi Arabia. Total required investment: "
                f"SAR {investment_sar:,.0f}, with projected IRR of {irr * 100:.1f}% and "
                f"NPV of SAR {npv_sar:,.0f}. The project is {vision_score}% aligned with "
                f"Vision 2030 targets and achieves Nitaqat {nitaqat_band.replace('_', ' ').title()} band. "
                f"Overall verdict: {verdict_en}."
            ),
            "top_recommendations_ar": [
                f"الانتهاء من تسجيل السجل التجاري والتراخيص اللازمة خلال 90 يوماً",
                f"الاستفادة من برامج صندوق تنمية الموارد البشرية (HRDF) لتخفيض تكاليف العمالة",
                f"استهداف نطاقات البلاتيني من خلال برنامج توطين مخطط له",
            ],
            "top_recommendations_en": [
                "Complete CR registration and licensing within 90 days",
                "Leverage HRDF subsidy programs to reduce Year 1 labor costs",
                "Target Nitaqat Platinum through a structured Saudization roadmap",
            ],
        }

    def _assemble_report_sections(self, data: dict) -> dict:
        sections_data = data.get("sections_data", data)
        report_template = data.get("report_template", "standard_sme")
        report = {
            "report_id": f"JADWA-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "report_template": report_template,
            "generated_at": datetime.utcnow().isoformat(),
            "sections": {},
        }

        section_order = [s for s in REPORT_SECTIONS if s != "executive_summary"]
        # executive_summary always first
        if "executive_summary" in sections_data:
            report["sections"]["executive_summary"] = sections_data["executive_summary"]

        for section in section_order:
            if section in sections_data:
                report["sections"][section] = sections_data[section]
            elif section not in ["franchise_analysis", "real_estate_analysis"]:
                report["sections"][section] = {
                    "status": "pending",
                    "note": f"Section '{section}' data not yet available.",
                }

        return report

    def _validate_report_completeness(self, data: dict) -> dict:
        report = data.get("report", data)
        required_sections = data.get("required_sections", None)
        if required_sections is None:
            required_sections = [
                s
                for s in REPORT_SECTIONS
                if s not in ["franchise_analysis", "real_estate_analysis"]
            ]

        present_sections = list(report.get("sections", {}).keys())
        missing = [s for s in required_sections if s not in present_sections]
        pending = [
            s
            for s in present_sections
            if report["sections"][s].get("status") == "pending"
        ]

        completeness_score = round(
            (len(required_sections) - len(missing) - len(pending))
            / len(required_sections)
            * 100
        )

        return {
            "completeness_score": completeness_score,
            "present_sections": present_sections,
            "missing_sections": missing,
            "pending_sections": pending,
            "is_complete": completeness_score >= 80,
        }

    def _build_user_message(self, context: dict) -> str:
        project_name = context.get(
            "business_name", context.get("project_name", "JADWA Project")
        )
        sector = context.get("sector", "default")
        investment = context.get("investment_amount_sar", 0)

        # Gather key metrics from agent outputs already in context
        financial = context.get("financial_model", {})
        irr = financial.get("irr", 0)
        npv = financial.get("npv_sar", 0)
        payback = financial.get("break_even_month", 0)
        vision_score = context.get("vision2030", {}).get("alignment_score", 75)
        risk_rating = context.get("risk_assessment", {}).get(
            "overall_risk_score", "medium"
        )
        nitaqat_band = context.get("hr_saudization", {}).get(
            "nitaqat_band", "low_green"
        )
        report_template = context.get("report_template", "standard_sme")

        return (
            f"Assemble the final JADWA feasibility report for: {project_name}\n"
            f"Sector: {sector} | Investment: SAR {investment:,.0f}\n\n"
            f"Steps:\n"
            f"1. Call compile_executive_summary with: project='{project_name}', "
            f"sector='{sector}', investment={investment}, irr={irr}, npv={npv}, "
            f"payback={payback}, vision_score={vision_score}, risk='{risk_rating}', "
            f"nitaqat='{nitaqat_band}'.\n"
            f"2. Call assemble_report_sections with all sections from context and template '{report_template}'.\n"
            f"3. Call validate_report_completeness on the assembled report.\n\n"
            f"Return the complete ReportDocument JSON with all sections.\n\n"
            f"All agent outputs:\n{json.dumps(context, ensure_ascii=False, indent=2)}"
        )
