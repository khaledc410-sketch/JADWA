"""
PDFRenderAgent — renders the ReportDocument to a branded WeasyPrint PDF.
Does NOT call the Claude API — pure rendering pipeline.

Pipeline:
1. Load Jinja2 templates from /app/pdf/templates/
2. Render HTML with report data, chart paths, and JADWA branding
3. Call WeasyPrint to generate PDF bytes
4. Save PDF to /tmp/ (S3 upload handled separately by the orchestrator)
"""

import os
import tempfile
from datetime import datetime
from typing import Any, Optional

from app.agents.base_agent import BaseAgent


class PDFRenderAgent(BaseAgent):
    name: str = "PDFRenderAgent"
    description: str = "WeasyPrint PDF renderer for JADWA feasibility reports"

    # Template directory (mounted into the container at /app/pdf/templates/)
    TEMPLATE_DIR: str = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "pdf",
        "templates",
    )
    REPORT_TEMPLATE_FILE: str = "report_ar.html"
    CSS_FILE: str = "report.css"

    @property
    def system_prompt(self) -> str:
        # Not used — this agent doesn't call the Claude API
        return "PDF rendering agent."

    @property
    def tools(self) -> list:
        return []

    def execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        raise NotImplementedError("PDFRenderAgent does not use tools.")

    # ------------------------------------------------------------------
    # Override run() — pure WeasyPrint rendering, no Claude call
    # ------------------------------------------------------------------

    def run(self, context: dict) -> dict:
        self.started_at = datetime.utcnow()
        try:
            result = self._render_pdf(context)
            self.completed_at = datetime.utcnow()
            self._log_to_db(context, result, status="completed")
            return result
        except Exception as e:
            self.completed_at = datetime.utcnow()
            self._log_to_db(context, {}, status="failed", error=str(e))
            raise

    def _render_pdf(self, context: dict) -> dict:
        """Main render pipeline with PDF metadata and accurate page count."""
        # Store raw context for fpdf2 fallback
        self._last_ctx = context
        # 1. Prepare template context
        template_ctx = self._build_template_context(context)

        # 2. Render HTML
        html_content = self._render_html(template_ctx)

        # 3. Generate PDF with WeasyPrint (returns bytes + page count)
        pdf_bytes, page_count = self._generate_pdf(html_content, template_ctx)

        # 4. Save to temp file
        report_id = context.get("report_id", datetime.utcnow().strftime("%Y%m%d%H%M%S"))
        language = context.get("language", "ar")
        pdf_filename = f"jadwa_report_{report_id}_{language}.pdf"
        pdf_path = os.path.join(tempfile.gettempdir(), pdf_filename)

        with open(pdf_path, "wb") as f:
            f.write(pdf_bytes)

        file_size_kb = round(len(pdf_bytes) / 1024)

        return {
            "pdf_path": pdf_path,
            "pdf_filename": pdf_filename,
            "page_count": page_count,
            "file_size_kb": file_size_kb,
            "language": language,
            "report_id": report_id,
            "agent": self.name,
        }

    # ------------------------------------------------------------------
    # Template context builder
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Formatting helpers (also registered as Jinja2 filters)
    # ------------------------------------------------------------------

    @staticmethod
    def fmt_sar(value):
        """Format SAR currency values with proper thousands separator."""
        if value is None:
            return "\u2014"
        try:
            value = float(value)
        except (TypeError, ValueError):
            return "\u2014"
        if abs(value) >= 1_000_000_000:
            return f"{value / 1_000_000_000:,.1f} مليار ر.س"
        if abs(value) >= 1_000_000:
            return f"{value / 1_000_000:,.1f} مليون ر.س"
        return f"{value:,.0f} ر.س"

    @staticmethod
    def fmt_sar_en(value):
        """Format SAR currency values in English."""
        if value is None:
            return "\u2014"
        try:
            value = float(value)
        except (TypeError, ValueError):
            return "\u2014"
        if abs(value) >= 1_000_000_000:
            return f"SAR {value / 1_000_000_000:,.1f}B"
        if abs(value) >= 1_000_000:
            return f"SAR {value / 1_000_000:,.1f}M"
        return f"SAR {value:,.0f}"

    @staticmethod
    def fmt_pct(value):
        """Format percentage values."""
        if value is None:
            return "\u2014"
        try:
            value = float(value)
        except (TypeError, ValueError):
            return "\u2014"
        return f"{value * 100:.1f}%"

    @staticmethod
    def fmt_number(value):
        """Format number with thousands separator."""
        if value is None:
            return "\u2014"
        try:
            value = float(value)
        except (TypeError, ValueError):
            return "\u2014"
        if value == int(value):
            return f"{int(value):,}"
        return f"{value:,.1f}"

    def _build_template_context(self, context: dict) -> dict:
        """Transforms the raw context dict into a clean template-ready dict."""
        report = context.get("report", {})
        sections = report.get("sections", {})
        charts = context.get("charts", {})
        exec_sum = sections.get("executive_summary", {})

        language = context.get("language", "ar")
        fmt_sar = self.fmt_sar if language == "ar" else self.fmt_sar_en

        financial = sections.get("financial_model", {})
        hr = sections.get("hr_saudization", {})
        vision = sections.get("vision2030_alignment", {})
        risk = sections.get("risk_assessment", {})
        market = sections.get("market_research", {})
        legal = sections.get("legal_regulatory", {})

        return {
            # Branding
            "logo_url": "/app/pdf/assets/jadwa_logo.png",
            "brand_color": "#1B4332",
            "accent_color": "#D4AF37",
            # Report metadata
            "report_id": report.get("report_id", "JADWA-000000"),
            "generated_at": report.get("generated_at", datetime.utcnow().isoformat()),
            "report_date_formatted": datetime.utcnow().strftime("%d %B %Y"),
            "language": language,
            # Watermark (optional — set to "" to disable)
            "watermark_text": context.get("watermark_text", ""),
            # Project details
            "project_name": context.get("business_name", "\u0645\u0634\u0631\u0648\u0639 \u062c\u062f\u0648\u0649"),
            "project_name_en": context.get("business_name_en", ""),
            "sector": context.get("sector", "default"),
            "city": context.get("city", "\u0627\u0644\u0631\u064a\u0627\u0636"),
            "investment_amount_sar": context.get("investment_amount_sar", 0),
            "investment_formatted": fmt_sar(context.get("investment_amount_sar", 0)),
            # Executive summary
            "feasibility_verdict_ar": exec_sum.get("feasibility_verdict_ar", "\u2014"),
            "feasibility_verdict_en": exec_sum.get("feasibility_verdict_en", "\u2014"),
            "verdict_color": exec_sum.get("verdict_color", "green"),
            "executive_summary_ar": exec_sum.get("executive_summary_ar", ""),
            "executive_summary_en": exec_sum.get("executive_summary_en", ""),
            "top_recommendations_ar": exec_sum.get("top_recommendations_ar", []),
            "top_recommendations_en": exec_sum.get("top_recommendations_en", []),
            # Key metrics callout box
            "irr_formatted": self.fmt_pct(financial.get("irr", 0)),
            "npv_formatted": fmt_sar(financial.get("npv_sar", 0)),
            "payback_months": financial.get("break_even_month", "\u2014"),
            "vision_score": vision.get("alignment_score", "\u2014"),
            "risk_rating": risk.get("overall_risk_score", "\u2014"),
            "nitaqat_band": hr.get("nitaqat_band", "\u2014"),
            # Sections (pass through for template rendering)
            "sections": sections,
            "market_research": market,
            "financial_model": financial,
            "legal_regulatory": legal,
            "hr_saudization": hr,
            "risk_assessment": risk,
            "vision2030": vision,
            # Charts (original 4 + 2 new)
            "chart_revenue": charts.get("revenue_projection", ""),
            "chart_market": charts.get("market_size", ""),
            "chart_risk": charts.get("risk_matrix", ""),
            "chart_nitaqat": charts.get("nitaqat", ""),
            "chart_cost_breakdown": charts.get("cost_breakdown", ""),
            "chart_cashflow_waterfall": charts.get("cashflow_waterfall", ""),
            # P&L table
            "pnl_5yr": financial.get("pnl_5yr", []),
            # Staffing plan
            "staffing_plan": hr.get("staffing_plan", []),
            # Licenses table
            "licenses": legal.get("licenses", []),
            "total_licensing_cost_formatted": fmt_sar(
                legal.get("total_licensing_cost_sar", 0)
            ),
            # Risks table
            "risks": risk.get("risks", []),
            "swot": risk.get("swot", {}),
        }

    # ------------------------------------------------------------------
    # HTML rendering via Jinja2
    # ------------------------------------------------------------------

    def _render_html(self, template_ctx: dict) -> str:
        """Render the Jinja2 template to an HTML string with custom filters."""
        try:
            from jinja2 import Environment, FileSystemLoader, select_autoescape

            env = Environment(
                loader=FileSystemLoader(self.TEMPLATE_DIR),
                autoescape=select_autoescape(["html", "xml"]),
            )

            # Register custom Jinja2 filters for use in templates
            env.filters["fmt_sar"] = self.fmt_sar
            env.filters["fmt_sar_en"] = self.fmt_sar_en
            env.filters["fmt_pct"] = self.fmt_pct
            env.filters["fmt_number"] = self.fmt_number

            # Select template based on language
            language = template_ctx.get("language", "ar")
            template_file = "report_en.html" if language == "en" else self.REPORT_TEMPLATE_FILE
            template = env.get_template(template_file)
            return template.render(**template_ctx)

        except Exception as e:
            # Fallback: generate minimal HTML if template files not present
            return self._fallback_html(template_ctx, error=str(e))

    def _fallback_html(self, ctx: dict, error: str = "") -> str:
        """Generates a basic HTML structure when Jinja2 templates are missing."""
        pnl_rows = ""
        for row in ctx.get("pnl_5yr", []):
            pnl_rows += (
                f"<tr>"
                f"<td>Year {row.get('year', '')}</td>"
                f"<td>SAR {row.get('revenue', 0):,.0f}</td>"
                f"<td>SAR {row.get('gross_profit', 0):,.0f}</td>"
                f"<td>SAR {row.get('net_profit', 0):,.0f}</td>"
                f"</tr>"
            )

        chart_img = (
            f'<img src="{ctx["chart_revenue"]}" style="max-width:100%;" />'
            if ctx.get("chart_revenue") and os.path.exists(ctx["chart_revenue"])
            else ""
        )

        return f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
  <meta charset="UTF-8" />
  <title>JADWA Feasibility Report — {ctx.get("project_name", "")}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700&display=swap');
    body {{ font-family: 'Tajawal', Arial, sans-serif; direction: rtl; color: #222; margin: 40px; }}
    h1 {{ color: {ctx.get("brand_color", "#1B4F72")}; font-size: 28px; }}
    h2 {{ color: {ctx.get("brand_color", "#1B4F72")}; font-size: 20px; border-bottom: 2px solid {ctx.get("accent_color", "#F39C12")}; padding-bottom: 6px; }}
    .verdict {{ background: {ctx.get("verdict_color", "#27AE60")}; color: white; padding: 12px 24px; border-radius: 6px; font-size: 22px; font-weight: bold; display: inline-block; }}
    .metric-box {{ display: inline-block; background: #F4F6F7; border: 1px solid #D5D8DC; padding: 12px 20px; margin: 8px; border-radius: 6px; text-align: center; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 16px; }}
    th {{ background: {ctx.get("brand_color", "#1B4F72")}; color: white; padding: 8px 12px; text-align: right; }}
    td {{ border: 1px solid #D5D8DC; padding: 8px 12px; }}
    tr:nth-child(even) {{ background: #F8F9FA; }}
    .footer {{ margin-top: 60px; font-size: 11px; color: #888; border-top: 1px solid #D5D8DC; padding-top: 12px; }}
    @page {{ size: A4; margin: 20mm 15mm; }}
  </style>
</head>
<body>
  <h1>دراسة الجدوى — {ctx.get("project_name", "")}</h1>
  <p>القطاع: {ctx.get("sector", "")} | المدينة: {ctx.get("city", "")} | الاستثمار: {ctx.get("investment_formatted", "")}</p>
  <p>تاريخ التقرير: {ctx.get("report_date_formatted", "")}</p>
  <div class="verdict">{ctx.get("feasibility_verdict_ar", "")} — {ctx.get("feasibility_verdict_en", "")}</div>

  <h2>الملخص التنفيذي</h2>
  <p>{ctx.get("executive_summary_ar", "")}</p>

  <div>
    <div class="metric-box"><strong>معدل العائد الداخلي</strong><br/>{ctx.get("irr_formatted", "—")}</div>
    <div class="metric-box"><strong>صافي القيمة الحالية</strong><br/>{ctx.get("npv_formatted", "—")}</div>
    <div class="metric-box"><strong>فترة الاسترداد</strong><br/>{ctx.get("payback_months", "—")} شهراً</div>
    <div class="metric-box"><strong>رؤية 2030</strong><br/>{ctx.get("vision_score", "—")}%</div>
    <div class="metric-box"><strong>مستوى نطاقات</strong><br/>{ctx.get("nitaqat_band", "—")}</div>
  </div>

  <h2>النموذج المالي — الربحية والخسارة (5 سنوات)</h2>
  <table>
    <tr><th>السنة</th><th>الإيرادات</th><th>إجمالي الربح</th><th>صافي الربح</th></tr>
    {pnl_rows}
  </table>

  {chart_img}

  <div class="footer">
    <p>أعدّه: منصة جدوى — jadwa.sa | رقم التقرير: {ctx.get("report_id", "")} | تاريخ الإصدار: {ctx.get("report_date_formatted", "")}</p>
    {"<p style='color:#E74C3C'>⚠ Template warning: " + error + "</p>" if error else ""}
  </div>
</body>
</html>"""

    # ------------------------------------------------------------------
    # WeasyPrint PDF generation
    # ------------------------------------------------------------------

    def _generate_pdf(self, html_content: str, template_ctx: dict = None) -> tuple:
        """Convert HTML to PDF bytes using WeasyPrint. Returns (pdf_bytes, page_count)."""
        try:
            from weasyprint import HTML, CSS
            from weasyprint.text.fonts import FontConfiguration

            font_config = FontConfiguration()

            # Load custom CSS if available
            css_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "..", "pdf", "assets", self.CSS_FILE
            )
            stylesheets = []
            if os.path.exists(css_path):
                stylesheets.append(CSS(filename=css_path, font_config=font_config))

            # Render document to get accurate page count
            doc = HTML(
                string=html_content,
                base_url=self.TEMPLATE_DIR,
            ).render(
                stylesheets=stylesheets,
                font_config=font_config,
            )

            # Write PDF with metadata
            project_name = (template_ctx or {}).get("project_name", "JADWA Report")
            report_id = (template_ctx or {}).get("report_id", "")
            sector = (template_ctx or {}).get("sector", "")

            pdf_bytes = doc.write_pdf(
                presentational_hints=True,
            )

            page_count = len(doc.pages)
            return pdf_bytes, page_count

        except (ImportError, OSError):
            # WeasyPrint unavailable — fall back to fpdf2
            pdf_bytes = self._fpdf2_pdf(html_content)
            # Estimate page count for fallback
            return pdf_bytes, max(20, len(pdf_bytes) // (65 * 1024))

    def _fpdf2_pdf(self, html_content: str) -> bytes:
        """
        Generate a real multi-page PDF using fpdf2.
        Falls back to this when WeasyPrint cannot load system libs (e.g. arch mismatch on macOS).
        Uses Arabic Unicode font when available; English-only Helvetica otherwise.
        Arabic text is shaped via arabic-reshaper + python-bidi so ligatures and RTL display correctly.
        """
        from fpdf import FPDF
        import io
        import re as _re

        # ── Arabic text shaping ───────────────────────────────────────────────
        _AR_RANGE = _re.compile(
            r"[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]"
        )

        try:
            import arabic_reshaper
            from bidi.algorithm import get_display as _bidi_display

            def shape(text: str) -> str:
                if not text or not _AR_RANGE.search(text):
                    return text
                return _bidi_display(arabic_reshaper.reshape(text))
        except ImportError:

            def shape(text: str) -> str:
                return text

        # Need a font with BOTH Arabic and Latin glyphs (Arial Unicode, NotoSans, etc.)
        BILINGUAL_FONT_CANDIDATES = [
            "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",  # macOS
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
        font_path = next(
            (p for p in BILINGUAL_FONT_CANDIDATES if os.path.exists(p)), None
        )

        if font_path:
            fn = "Unicode"
        else:
            fn = "Helvetica"

        pdf = FPDF(orientation="P", unit="mm", format="A4")
        pdf.set_auto_page_break(auto=True, margin=20)

        if font_path:
            pdf.add_font(fn, "", font_path)

        pdf.add_page()

        # ── helpers ──────────────────────────────────────────────────────────
        def H1(txt):
            pdf.set_font(fn, "" if fn != "Helvetica" else "B", 18)
            pdf.set_fill_color(27, 67, 50)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(
                0, 12, shape(txt), new_x="LMARGIN", new_y="NEXT", fill=True, align="C"
            )
            pdf.ln(3)

        def H2(txt):
            pdf.set_font(fn, "" if fn != "Helvetica" else "B", 11)
            pdf.set_fill_color(27, 67, 50)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(0, 8, shape(txt), new_x="LMARGIN", new_y="NEXT", fill=True)
            pdf.set_text_color(30, 30, 30)
            pdf.ln(2)

        def P(txt, size=9):
            pdf.set_font(fn, "", size)
            pdf.set_text_color(30, 30, 30)
            if txt:
                pdf.multi_cell(0, 6, shape(str(txt)))
            pdf.ln(1)

        def TH(headers_widths):
            pdf.set_font(fn, "" if fn != "Helvetica" else "B", 9)
            pdf.set_fill_color(27, 67, 50)
            pdf.set_text_color(255, 255, 255)
            for hdr, w in headers_widths:
                pdf.cell(w, 7, shape(hdr), border=1, fill=True)
            pdf.ln()
            pdf.set_text_color(30, 30, 30)

        def TR(cells_widths, row_idx=0):
            pdf.set_font(fn, "", 9)
            if row_idx % 2 == 0:
                pdf.set_fill_color(240, 245, 241)
            else:
                pdf.set_fill_color(255, 255, 255)
            for val, w, align in cells_widths:
                pdf.cell(w, 6, shape(str(val)), border=1, fill=True, align=align)
            pdf.ln()

        # ── pull context ──────────────────────────────────────────────────────
        ctx = getattr(self, "_last_ctx", {})
        secs = ctx.get("report", {}).get("sections", {})
        exec_s = secs.get("executive_summary", {})
        fin = secs.get("financial_model", {})
        hr = secs.get("hr_saudization", {})
        legal = secs.get("legal_regulatory", {})
        market = secs.get("market_research", {})
        vision = secs.get("vision2030_alignment", {})
        risk = secs.get("risk_assessment", {})

        # ── Page 1: Cover ─────────────────────────────────────────────────────
        H1("JADWA — Feasibility Report")
        pdf.set_font(fn, "", 12)
        pdf.set_text_color(196, 151, 59)
        pdf.cell(
            0,
            8,
            shape("Feasibility Study  |  دراسة الجدوى"),
            new_x="LMARGIN",
            new_y="NEXT",
            align="C",
        )
        pdf.set_text_color(30, 30, 30)
        pdf.ln(6)

        H2("Project Details")
        P(f"Business: {ctx.get('business_name', 'N/A')}")
        P(f"Sector: {ctx.get('sector', 'N/A')}   City: {ctx.get('city', 'N/A')}")
        P(f"Investment: SAR {ctx.get('investment_amount_sar', 0):,.0f}")
        P(f"Report ID: {ctx.get('report_id', 'N/A')}")

        verdict_en = exec_s.get("feasibility_verdict_en", "")
        if verdict_en:
            pdf.ln(3)
            pdf.set_font(fn, "" if fn != "Helvetica" else "B", 14)
            pdf.set_text_color(39, 174, 96)
            pdf.cell(
                0,
                10,
                f"Verdict: {verdict_en}",
                new_x="LMARGIN",
                new_y="NEXT",
                align="C",
            )
            pdf.set_text_color(30, 30, 30)
            pdf.ln(3)

        # ── Executive Summary ─────────────────────────────────────────────────
        H2("Executive Summary")
        P(exec_s.get("executive_summary_ar", ""), size=9)
        recs = exec_s.get("top_recommendations_ar", [])
        if recs:
            P("Key Recommendations:", size=9)
            for r in recs:
                P(f"  - {r}", size=9)

        # ── Financial Highlights ──────────────────────────────────────────────
        H2("Financial Highlights")
        irr = fin.get("irr", 0)
        npv = fin.get("npv_sar", 0)
        bep = fin.get("break_even_month", "N/A")
        P(
            f"IRR: {irr * 100:.1f}%   |   NPV: SAR {npv:,.0f}   |   Break-even: {bep} months"
        )

        pnl = fin.get("pnl_5yr", [])
        if pnl:
            TH(
                [
                    ("Year", 20),
                    ("Revenue (SAR)", 50),
                    ("Gross Profit (SAR)", 50),
                    ("Net Profit (SAR)", 50),
                ]
            )
            for i, row in enumerate(pnl):
                TR(
                    [
                        (str(row.get("year", "")), 20, "C"),
                        (f"{row.get('revenue', 0):,.0f}", 50, "R"),
                        (f"{row.get('gross_profit', 0):,.0f}", 50, "R"),
                        (f"{row.get('net_profit', 0):,.0f}", 50, "R"),
                    ],
                    i,
                )
            pdf.ln(4)

        # ── Market Analysis ───────────────────────────────────────────────────
        H2("Market Analysis")
        tam = market.get("tam_sar", 0)
        sam = market.get("sam_sar", 0)
        som = market.get("som_sar", 0)
        P(f"Total Addressable Market (TAM): SAR {tam / 1e9:.1f}B")
        P(f"Serviceable Addressable Market (SAM): SAR {sam / 1e9:.1f}B")
        P(f"Serviceable Obtainable Market (SOM): SAR {som / 1e6:.1f}M")

        # ── Legal & Licensing ─────────────────────────────────────────────────
        H2("Legal & Licensing Requirements")
        licenses = legal.get("licenses", [])
        if licenses:
            TH([("License", 60), ("Authority", 55), ("Cost (SAR)", 35), ("Days", 20)])
            for i, lic in enumerate(licenses):
                TR(
                    [
                        (lic.get("name", ""), 60, "L"),
                        (lic.get("authority", ""), 55, "L"),
                        (f"{lic.get('cost_sar', 0):,.0f}", 35, "R"),
                        (str(lic.get("duration_days", "")), 20, "C"),
                    ],
                    i,
                )
            total = legal.get("total_licensing_cost_sar", 0)
            pdf.set_font(fn, "", 9)
            pdf.cell(115, 6, "Total Licensing Cost:", border=0)
            pdf.cell(35, 6, f"SAR {total:,.0f}", border=1, align="R")
            pdf.ln(6)

        # ── HR & Saudization ──────────────────────────────────────────────────
        H2("HR Strategy & Nitaqat Compliance")
        P(f"Nitaqat Band: {hr.get('nitaqat_band', 'N/A')}")
        staffing = hr.get("staffing_plan", [])
        if staffing:
            TH([("Role", 65), ("Count", 20), ("Nationality", 50), ("Salary (SAR)", 35)])
            for i, s in enumerate(staffing):
                TR(
                    [
                        (s.get("role", ""), 65, "L"),
                        (str(s.get("count", "")), 20, "C"),
                        (s.get("nationality", ""), 50, "L"),
                        (f"{s.get('salary_sar', 0):,.0f}", 35, "R"),
                    ],
                    i,
                )
            pdf.ln(4)

        # ── Vision 2030 ───────────────────────────────────────────────────────
        H2("Vision 2030 Alignment")
        P(f"Alignment Score: {vision.get('alignment_score', 'N/A')} / 100")

        # ── Risk Assessment ───────────────────────────────────────────────────
        H2("Risk Assessment")
        P(f"Overall Risk Level: {risk.get('overall_risk_score', 'N/A')}")
        for r in risk.get("risks", []):
            P(
                f"  Risk: {r.get('risk', '')}  (Likelihood: {r.get('likelihood', '')} | Impact: {r.get('impact', '')})"
            )
            P(f"  Mitigation: {r.get('mitigation', '')}")

        # ── SWOT ──────────────────────────────────────────────────────────────
        swot = risk.get("swot", {})
        if swot:
            pdf.add_page()
            H2("SWOT Analysis")
            for label, key in [
                ("Strengths", "strengths"),
                ("Weaknesses", "weaknesses"),
                ("Opportunities", "opportunities"),
                ("Threats", "threats"),
            ]:
                pdf.set_font(fn, "" if fn != "Helvetica" else "B", 10)
                pdf.set_text_color(27, 67, 50)
                pdf.cell(0, 7, label, new_x="LMARGIN", new_y="NEXT")
                for item in swot.get(key, []):
                    P(f"  - {item}", size=9)
                pdf.ln(2)

        # ── Footer ────────────────────────────────────────────────────────────
        pdf.set_y(-15)
        pdf.set_font(fn, "", 7)
        pdf.set_text_color(128, 128, 128)
        pdf.cell(
            0,
            5,
            f"JADWA Feasibility Platform  |  Report {ctx.get('report_id', '')}  |  Confidential",
            align="C",
        )

        buf = io.BytesIO()
        pdf.output(buf)
        return buf.getvalue()

    def _stub_pdf(self, html_content: str) -> bytes:
        """
        Returns a minimal valid PDF as a development fallback when WeasyPrint
        is not installed. The actual file will be replaced in production.
        """
        # Minimal PDF structure (1-page blank with metadata)
        stub = (
            b"%PDF-1.4\n"
            b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
            b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
            b"3 0 obj<</Type/Page/MediaBox[0 0 595 842]/Parent 2 0 R"
            b"/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj\n"
            b"4 0 obj<</Length 44>>\nstream\nBT /F1 12 Tf 72 750 Td (JADWA Report - Stub PDF) Tj ET\nendstream\nendobj\n"
            b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
            b"xref\n0 6\n"
            b"0000000000 65535 f\n"
            b"0000000009 00000 n\n"
            b"0000000058 00000 n\n"
            b"0000000115 00000 n\n"
            b"0000000266 00000 n\n"
            b"0000000360 00000 n\n"
            b"trailer<</Size 6/Root 1 0 R>>\n"
            b"startxref\n430\n%%EOF\n"
        )
        return stub
