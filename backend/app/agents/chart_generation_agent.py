"""
ChartGenerationAgent — generates Matplotlib chart PNG files directly from
structured financial and market data. Does NOT call the Claude API.

Premium chart styling with JADWA brand identity (Saudi green + gold).
All charts rendered at 300 DPI for print-quality PDF output.
"""

import io
import os
import tempfile
from datetime import datetime
from typing import Any, Optional

from app.agents.base_agent import BaseAgent


# ── Brand constants ──────────────────────────────────────────────────────
BRAND_PRIMARY = "#1B4332"
BRAND_PRIMARY_MID = "#2D6A4F"
BRAND_SECONDARY = "#40916C"
BRAND_SECONDARY_LIGHT = "#52B788"
BRAND_ACCENT = "#D4AF37"
BRAND_ACCENT_BRIGHT = "#F0C040"
BRAND_RED = "#C53030"
BRAND_ORANGE = "#B7791F"
BRAND_BLUE = "#2B6CB0"
BRAND_PURPLE = "#805AD5"
BRAND_BG = "#FAFBFC"
BRAND_WHITE = "#FFFFFF"
BRAND_TEXT = "#1A202C"
BRAND_TEXT_MUTED = "#718096"
CHART_DPI = 300


class ChartGenerationAgent(BaseAgent):
    name: str = "ChartGenerationAgent"
    description: str = "Generates premium Matplotlib PNG charts from financial and market data"

    @property
    def system_prompt(self) -> str:
        return "Data visualization specialist."

    @property
    def tools(self) -> list:
        return []

    def execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        raise NotImplementedError("ChartGenerationAgent does not use tools.")

    # ------------------------------------------------------------------
    # Override run() — generate charts using Matplotlib, no Claude call
    # ------------------------------------------------------------------

    def run(self, context: dict) -> dict:
        self.started_at = datetime.utcnow()
        try:
            charts = {}
            charts["revenue_projection"] = self._revenue_projection_chart(context)
            charts["market_size"] = self._market_size_chart(context)
            charts["risk_matrix"] = self._risk_matrix_chart(context)
            charts["nitaqat"] = self._nitaqat_chart(context)
            charts["cost_breakdown"] = self._cost_breakdown_chart(context)
            charts["cashflow_waterfall"] = self._cashflow_waterfall_chart(context)

            result = {"charts": charts, "agent": self.name}
            self.completed_at = datetime.utcnow()
            self._log_to_db(context, result, status="completed")
            return result
        except Exception as e:
            self.completed_at = datetime.utcnow()
            self._log_to_db(context, {}, status="failed", error=str(e))
            raise

    # ------------------------------------------------------------------
    # Brand styling helper
    # ------------------------------------------------------------------

    def _apply_brand_style(self, fig, ax, title: str = "", subtitle: str = ""):
        """Apply consistent JADWA brand styling to any chart."""
        ax.set_facecolor(BRAND_BG)
        fig.patch.set_facecolor(BRAND_WHITE)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#E2E8F0")
        ax.spines["bottom"].set_color("#E2E8F0")
        ax.tick_params(colors=BRAND_TEXT, labelsize=9)
        ax.grid(True, alpha=0.15, linestyle="--", color="#CBD5E0")
        if title:
            ax.set_title(
                title,
                fontsize=13,
                fontweight="bold",
                color=BRAND_PRIMARY,
                pad=18,
                loc="left",
            )
        if subtitle:
            ax.text(
                0.0, 1.06, subtitle,
                transform=ax.transAxes,
                fontsize=9,
                color=BRAND_TEXT_MUTED,
                style="italic",
            )

    def _save_chart(self, fig, filename: str) -> str:
        """Save chart at print-quality DPI."""
        import matplotlib.pyplot as plt

        path = self._get_tmp_path(filename)
        fig.savefig(path, dpi=CHART_DPI, bbox_inches="tight", facecolor=fig.get_facecolor())
        plt.close(fig)
        return path

    # ------------------------------------------------------------------
    # Individual chart generators
    # ------------------------------------------------------------------

    def _get_tmp_path(self, filename: str) -> str:
        return os.path.join(tempfile.gettempdir(), filename)

    def _revenue_projection_chart(self, context: dict) -> str:
        """5-year revenue vs costs line chart — premium brand styling."""
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.ticker as mticker

        pnl_5yr = context.get("financial_model", {}).get("pnl_5yr", [])
        if not pnl_5yr:
            investment = context.get("investment_amount_sar", 2_000_000)
            base_rev = investment * 1.5
            pnl_5yr = [
                {
                    "year": i + 1,
                    "revenue": round(base_rev * (1.12**i) * (0.65 if i == 0 else 1)),
                    "cogs": round(base_rev * (1.12**i) * (0.65 if i == 0 else 1) * 0.40),
                    "opex": round(base_rev * (1.12**i) * (0.65 if i == 0 else 1) * 0.35),
                    "net_profit": round(base_rev * (1.12**i) * (0.65 if i == 0 else 1) * 0.10),
                }
                for i in range(5)
            ]

        years = [f"Year {r['year']}" for r in pnl_5yr]
        revenues = [r["revenue"] / 1_000_000 for r in pnl_5yr]
        total_costs = [(r.get("cogs", 0) + r.get("opex", 0)) / 1_000_000 for r in pnl_5yr]
        net_profits = [r.get("net_profit", 0) / 1_000_000 for r in pnl_5yr]

        fig, ax = plt.subplots(figsize=(8, 5))

        # Revenue line with area fill
        ax.plot(years, revenues, marker="o", linewidth=2.5, color=BRAND_PRIMARY,
                label="Revenue / الإيرادات", markersize=8, zorder=5)
        ax.fill_between(years, revenues, alpha=0.08, color=BRAND_PRIMARY)

        # Total costs line
        ax.plot(years, total_costs, marker="s", linewidth=2.5, color=BRAND_RED,
                label="Total Costs / التكاليف", markersize=7, zorder=5)

        # Net profit line with area fill
        ax.plot(years, net_profits, marker="D", linewidth=2.5, color=BRAND_SECONDARY,
                label="Net Profit / صافي الربح", markersize=7, linestyle="--", zorder=5)
        ax.fill_between(years, net_profits, alpha=0.12, color=BRAND_SECONDARY)

        # Data labels on each point
        for i, (rev, cost, profit) in enumerate(zip(revenues, total_costs, net_profits)):
            ax.annotate(f"{rev:.1f}M", (years[i], rev), textcoords="offset points",
                        xytext=(0, 12), ha="center", fontsize=7.5, fontweight="bold",
                        color=BRAND_PRIMARY)
            ax.annotate(f"{profit:.1f}M", (years[i], profit), textcoords="offset points",
                        xytext=(0, -14), ha="center", fontsize=7.5, fontweight="bold",
                        color=BRAND_SECONDARY)

        self._apply_brand_style(fig, ax,
                                title="5-Year Revenue & Profitability Projection",
                                subtitle="توقعات الإيرادات والربحية لخمس سنوات")
        ax.set_xlabel("Year / السنة", fontsize=10, color=BRAND_TEXT_MUTED)
        ax.set_ylabel("SAR Millions / مليون ريال", fontsize=10, color=BRAND_TEXT_MUTED)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"SAR {x:.1f}M"))
        ax.legend(fontsize=9, framealpha=0.9, edgecolor="#E2E8F0", loc="upper left")
        plt.tight_layout()

        return self._save_chart(fig, "chart_revenue.png")

    def _market_size_chart(self, context: dict) -> str:
        """TAM/SAM/SOM funnel bar chart — descending widths for funnel effect."""
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.ticker as mticker

        market = context.get("market_research", {})
        tam = market.get("tam", {}).get("value_sar", 100_000_000_000)
        sam = market.get("sam", {}).get("value_sar", 15_000_000_000)
        som = market.get("som", {}).get("value_sar", 750_000_000)

        values_bn = [tam / 1e9, sam / 1e9, som / 1e9]
        labels = ["TAM\nTotal Addressable\nإجمالي السوق", "SAM\nServiceable\nالسوق القابل للخدمة", "SOM\nObtainable\nالسوق المستهدف"]
        colors = [BRAND_PRIMARY, BRAND_SECONDARY, BRAND_ACCENT]
        widths = [0.7, 0.55, 0.4]

        fig, ax = plt.subplots(figsize=(8, 5))
        for i, (label, val, color, w) in enumerate(zip(labels, values_bn, colors, widths)):
            bar = ax.bar(i, val, color=color, width=w, edgecolor="white", linewidth=2,
                         alpha=0.9, zorder=3)
            # Value label above bar
            ax.text(i, val + max(values_bn) * 0.02,
                    f"SAR {val:.1f}B", ha="center", va="bottom",
                    fontweight="bold", fontsize=10, color=color)
            # Percentage label
            if i > 0:
                pct = val / values_bn[i - 1] * 100
                ax.text(i, val / 2, f"{pct:.0f}%\nof prev",
                        ha="center", va="center", fontsize=8,
                        color="white", fontweight="bold")

        ax.set_xticks(range(3))
        ax.set_xticklabels(labels, fontsize=8.5)
        self._apply_brand_style(fig, ax,
                                title="Market Size Analysis — TAM / SAM / SOM",
                                subtitle="تحليل حجم السوق — إجمالي، قابل للخدمة، مستهدف")
        ax.set_ylabel("SAR Billions / مليار ريال", fontsize=10, color=BRAND_TEXT_MUTED)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"SAR {x:.0f}B"))
        ax.grid(axis="y", alpha=0.15, linestyle="--")
        plt.tight_layout()

        return self._save_chart(fig, "chart_market.png")

    def _risk_matrix_chart(self, context: dict) -> str:
        """Likelihood vs impact scatter plot — premium risk matrix with quadrant labels."""
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
        from matplotlib.patches import FancyBboxPatch

        risks = context.get("risk_assessment", {}).get("risks", [])
        if not risks:
            risks = [
                {"id": "R001", "category": "market", "likelihood": 3, "impact": 4, "description_en": "Oil price volatility"},
                {"id": "R002", "category": "regulatory", "likelihood": 3, "impact": 3, "description_en": "Regulatory changes"},
                {"id": "R003", "category": "financial", "likelihood": 2, "impact": 3, "description_en": "Currency risk"},
                {"id": "R004", "category": "operational", "likelihood": 4, "impact": 3, "description_en": "Talent shortage"},
                {"id": "R005", "category": "market", "likelihood": 4, "impact": 3, "description_en": "Competition"},
                {"id": "R006", "category": "financial", "likelihood": 3, "impact": 3, "description_en": "Interest rate risk"},
            ]

        category_colors = {
            "market": BRAND_RED,
            "financial": BRAND_ORANGE,
            "regulatory": BRAND_PURPLE,
            "operational": BRAND_BLUE,
        }

        fig, ax = plt.subplots(figsize=(8, 6.5))

        # Smooth heat zone backgrounds with diagonal gradient effect
        import numpy as np
        x = np.linspace(0.5, 5.5, 100)
        y = np.linspace(0.5, 5.5, 100)
        X, Y = np.meshgrid(x, y)
        Z = (X + Y) / 2
        ax.contourf(X, Y, Z, levels=[0, 3, 4.5, 6, 10],
                     colors=["#E8F5E9", "#FFF8E1", "#FFF3E0", "#FFEBEE"],
                     alpha=0.5, zorder=0)

        # Quadrant labels
        ax.text(1.5, 1.3, "LOW RISK\nمخاطر منخفضة", ha="center", va="center",
                fontsize=7.5, color="#388E3C", alpha=0.6, fontweight="bold")
        ax.text(4.5, 1.3, "MEDIUM\nمتوسطة", ha="center", va="center",
                fontsize=7.5, color=BRAND_ORANGE, alpha=0.6, fontweight="bold")
        ax.text(1.5, 4.8, "MEDIUM\nمتوسطة", ha="center", va="center",
                fontsize=7.5, color=BRAND_ORANGE, alpha=0.6, fontweight="bold")
        ax.text(4.5, 4.8, "CRITICAL\nحرجة", ha="center", va="center",
                fontsize=7.5, color=BRAND_RED, alpha=0.6, fontweight="bold")

        # Plot risks as larger bubbles with ID inside
        for risk in risks:
            cat = risk.get("category", "market")
            color = category_colors.get(cat, "#7F8C8D")
            ax.scatter(risk["likelihood"], risk["impact"], s=350, color=color,
                       zorder=5, edgecolors="white", linewidth=2, alpha=0.9)
            ax.text(risk["likelihood"], risk["impact"], risk["id"],
                    ha="center", va="center", fontsize=7, color="white",
                    fontweight="bold", zorder=6)

        ax.set_xlim(0.5, 5.5)
        ax.set_ylim(0.5, 5.5)
        ax.set_xticks([1, 2, 3, 4, 5])
        ax.set_yticks([1, 2, 3, 4, 5])
        ax.set_xticklabels(["1\nRare", "2\nUnlikely", "3\nPossible", "4\nLikely", "5\nAlmost\nCertain"], fontsize=8)
        ax.set_yticklabels(["1\nNegligible", "2\nMinor", "3\nModerate", "4\nMajor", "5\nCatastrophic"], fontsize=8)
        ax.set_xlabel("Likelihood / الاحتمالية", fontsize=10, color=BRAND_TEXT_MUTED)
        ax.set_ylabel("Impact / الأثر", fontsize=10, color=BRAND_TEXT_MUTED)

        # Grid at integer values
        ax.set_xticks([1.5, 2.5, 3.5, 4.5], minor=True)
        ax.set_yticks([1.5, 2.5, 3.5, 4.5], minor=True)
        ax.grid(which="minor", alpha=0.1, linestyle="-", color="#CBD5E0")

        self._apply_brand_style(fig, ax,
                                title="Risk Matrix — Likelihood vs. Impact",
                                subtitle="مصفوفة المخاطر — الاحتمالية مقابل الأثر")

        legend_patches = [mpatches.Patch(color=c, label=cat.title()) for cat, c in category_colors.items()]
        ax.legend(handles=legend_patches, loc="upper left", fontsize=8,
                  framealpha=0.9, edgecolor="#E2E8F0")
        plt.tight_layout()

        return self._save_chart(fig, "chart_risk.png")

    def _nitaqat_chart(self, context: dict) -> str:
        """Saudi vs expat workforce — premium stacked bar with compliance indicator."""
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        hr_data = context.get("hr_saudization", {})
        staffing = hr_data.get("staffing_plan", [])

        if staffing:
            saudi_count = sum(r.get("count", 1) for r in staffing if r.get("is_saudi"))
            expat_count = sum(r.get("count", 1) for r in staffing if not r.get("is_saudi"))
            total = saudi_count + expat_count
            nitaqat_pct = round(saudi_count / total * 100, 1) if total else 0
            nitaqat_band = hr_data.get("nitaqat_band", "low_green")
        else:
            saudi_count, expat_count, total = 8, 4, 12
            nitaqat_pct, nitaqat_band = 66.7, "platinum"

        band_colors = {
            "platinum": "#6B46C1", "high_green": BRAND_PRIMARY,
            "low_green": BRAND_SECONDARY, "yellow": BRAND_ORANGE, "red": BRAND_RED,
        }
        band_color = band_colors.get(nitaqat_band, "#95A5A6")
        band_label = nitaqat_band.replace("_", " ").title()

        fig, ax = plt.subplots(figsize=(8, 4))

        # Stacked horizontal bars
        ax.barh(["Workforce\nالقوى العاملة"], [saudi_count], color=BRAND_PRIMARY,
                label=f"Saudi / سعودي ({saudi_count})", height=0.45, zorder=3)
        ax.barh(["Workforce\nالقوى العاملة"], [expat_count], left=[saudi_count],
                color="#B7E4C7", label=f"Expat / وافد ({expat_count})", height=0.45, zorder=3)

        # Labels inside bars
        if saudi_count > 0:
            ax.text(saudi_count / 2, 0, f"{saudi_count}\n({nitaqat_pct:.0f}%)",
                    ha="center", va="center", color="white", fontweight="bold", fontsize=11)
        if expat_count > 0:
            expat_pct = 100 - nitaqat_pct
            ax.text(saudi_count + expat_count / 2, 0, f"{expat_count}\n({expat_pct:.0f}%)",
                    ha="center", va="center", color=BRAND_PRIMARY, fontweight="bold", fontsize=11)

        # Saudization target threshold line
        target_pct = 0.40
        target_x = total * target_pct
        ax.axvline(x=target_x, color=BRAND_RED, linestyle="--", linewidth=1.5, alpha=0.7, zorder=4)
        ax.text(target_x, 0.35, f"Target {target_pct:.0%}", ha="center", va="bottom",
                fontsize=8, color=BRAND_RED, fontweight="bold")

        # Band indicator badge
        ax.text(total + 0.3, 0, f"Band\n{band_label}", ha="left", va="center",
                fontsize=9, fontweight="bold", color=band_color,
                bbox=dict(boxstyle="round,pad=0.4", facecolor=band_color, alpha=0.12, edgecolor=band_color))

        self._apply_brand_style(fig, ax,
                                title=f"Nitaqat (نطاقات) Saudization — {nitaqat_pct}% Saudi",
                                subtitle="نسبة السعودة ومستوى نطاقات")
        ax.set_xlim(0, total + 3)
        ax.set_xlabel("Number of Employees / عدد الموظفين", fontsize=10, color=BRAND_TEXT_MUTED)
        ax.legend(loc="lower right", fontsize=8, framealpha=0.9, edgecolor="#E2E8F0")
        plt.tight_layout()

        return self._save_chart(fig, "chart_nitaqat.png")

    # ------------------------------------------------------------------
    # New charts — Cost Breakdown Donut & Cash Flow Waterfall
    # ------------------------------------------------------------------

    def _cost_breakdown_chart(self, context: dict) -> str:
        """Donut chart showing COGS, OPEX, Zakat cost breakdown."""
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        financial = context.get("financial_model", {})
        pnl_5yr = financial.get("pnl_5yr", [])

        if pnl_5yr:
            # Use Year 1 data for breakdown
            yr1 = pnl_5yr[0]
            cogs = yr1.get("cogs", 0)
            opex = yr1.get("opex", 0)
            zakat = yr1.get("zakat", 0)
        else:
            investment = context.get("investment_amount_sar", 2_000_000)
            cogs = round(investment * 1.5 * 0.65 * 0.40)
            opex = round(investment * 1.5 * 0.65 * 0.35)
            zakat = round(investment * 1.5 * 0.65 * 0.025)

        if zakat == 0:
            zakat = round((cogs + opex) * 0.025)

        values = [cogs, opex, zakat]
        labels = ["COGS\nتكلفة البضاعة", "OPEX\nمصاريف تشغيلية", "Zakat\nزكاة"]
        colors = [BRAND_PRIMARY, BRAND_SECONDARY, BRAND_ACCENT]
        total = sum(values)

        fig, ax = plt.subplots(figsize=(6, 6))

        wedges, texts, autotexts = ax.pie(
            values, labels=None, colors=colors, autopct=lambda p: f"{p:.0f}%",
            startangle=90, pctdistance=0.78, wedgeprops=dict(width=0.35, edgecolor="white", linewidth=3),
        )

        for at in autotexts:
            at.set_fontsize(10)
            at.set_fontweight("bold")
            at.set_color("white")

        # Center text
        ax.text(0, 0.05, f"SAR {total / 1_000_000:.1f}M", ha="center", va="center",
                fontsize=14, fontweight="bold", color=BRAND_PRIMARY)
        ax.text(0, -0.1, "Total Costs\nإجمالي التكاليف", ha="center", va="center",
                fontsize=8, color=BRAND_TEXT_MUTED)

        # Legend
        legend_labels = [f"{lbl} — SAR {val / 1_000_000:.1f}M" for lbl, val in zip(labels, values)]
        ax.legend(wedges, legend_labels, loc="lower center", fontsize=8,
                  framealpha=0.9, edgecolor="#E2E8F0", ncol=1,
                  bbox_to_anchor=(0.5, -0.08))

        ax.set_title("Year 1 Cost Breakdown\nتوزيع تكاليف السنة الأولى",
                      fontsize=13, fontweight="bold", color=BRAND_PRIMARY, pad=15)
        fig.patch.set_facecolor(BRAND_WHITE)
        plt.tight_layout()

        return self._save_chart(fig, "chart_cost_breakdown.png")

    def _cashflow_waterfall_chart(self, context: dict) -> str:
        """Waterfall chart showing cumulative cash flow with break-even highlight."""
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np

        financial = context.get("financial_model", {})
        pnl_5yr = financial.get("pnl_5yr", [])
        investment = context.get("investment_amount_sar", 2_000_000)

        if not pnl_5yr:
            base_rev = investment * 1.5
            pnl_5yr = [
                {"year": i + 1, "net_profit": round(base_rev * (1.12**i) * (0.65 if i == 0 else 1) * 0.10)}
                for i in range(5)
            ]

        # Build waterfall: initial investment (negative) + yearly net profits
        labels = ["Investment\nاستثمار"] + [f"Year {r['year']}\nالسنة {r['year']}" for r in pnl_5yr] + ["Cumulative\nالإجمالي"]
        values = [-investment] + [r.get("net_profit", 0) for r in pnl_5yr]
        cumulative = np.cumsum(values)
        total_cumulative = cumulative[-1]
        values.append(total_cumulative)

        fig, ax = plt.subplots(figsize=(8, 5))

        bottoms = [0]
        for i in range(1, len(values) - 1):
            bottoms.append(cumulative[i - 1])
        bottoms.append(0)

        colors_list = []
        for i, v in enumerate(values):
            if i == len(values) - 1:
                colors_list.append(BRAND_PRIMARY if v >= 0 else BRAND_RED)
            elif v >= 0:
                colors_list.append(BRAND_SECONDARY)
            else:
                colors_list.append(BRAND_RED)

        bars = ax.bar(range(len(values)), values, bottom=bottoms,
                      color=colors_list, width=0.6, edgecolor="white", linewidth=1.5, zorder=3)

        # Value labels
        for i, (bar, v, b) in enumerate(zip(bars, values, bottoms)):
            y_pos = b + v + (abs(max(values)) * 0.02 if v >= 0 else -abs(max(values)) * 0.02)
            va = "bottom" if v >= 0 else "top"
            ax.text(i, y_pos, f"SAR {v / 1_000_000:.1f}M", ha="center", va=va,
                    fontsize=7.5, fontweight="bold", color=colors_list[i])

        # Connector lines between bars
        for i in range(len(values) - 2):
            ax.plot([i + 0.3, i + 0.7], [cumulative[i], cumulative[i]],
                    color="#CBD5E0", linewidth=1, linestyle="-", zorder=2)

        # Break-even line
        ax.axhline(y=0, color="#1A202C", linewidth=0.8, linestyle="-", alpha=0.3)

        # Find break-even year
        for i, c in enumerate(cumulative):
            if c >= 0 and i > 0:
                ax.annotate("Break-even\nنقطة التعادل", xy=(i + 0.5, 0),
                            fontsize=8, color=BRAND_ACCENT, fontweight="bold",
                            ha="center", va="bottom",
                            arrowprops=dict(arrowstyle="->", color=BRAND_ACCENT, lw=1.5))
                break

        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, fontsize=7.5)
        self._apply_brand_style(fig, ax,
                                title="Cumulative Cash Flow Waterfall",
                                subtitle="شلال التدفقات النقدية التراكمية")
        ax.set_ylabel("SAR / ريال سعودي", fontsize=10, color=BRAND_TEXT_MUTED)
        import matplotlib.ticker as mticker
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"SAR {x / 1_000_000:.1f}M"))
        plt.tight_layout()

        return self._save_chart(fig, "chart_cashflow_waterfall.png")
