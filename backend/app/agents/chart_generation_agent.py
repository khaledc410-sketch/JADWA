"""
ChartGenerationAgent — generates Matplotlib chart PNG files directly from
structured financial and market data. Does NOT call the Claude API.
"""

import io
import os
import tempfile
from datetime import datetime
from typing import Any, Optional

from app.agents.base_agent import BaseAgent


class ChartGenerationAgent(BaseAgent):
    name: str = "ChartGenerationAgent"
    description: str = "Generates Matplotlib PNG charts from financial and market data"

    @property
    def system_prompt(self) -> str:
        # Not used — this agent doesn't call the Claude API
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

            result = {"charts": charts, "agent": self.name}
            self.completed_at = datetime.utcnow()
            self._log_to_db(context, result, status="completed")
            return result
        except Exception as e:
            self.completed_at = datetime.utcnow()
            self._log_to_db(context, {}, status="failed", error=str(e))
            raise

    # ------------------------------------------------------------------
    # Individual chart generators
    # ------------------------------------------------------------------

    def _get_tmp_path(self, filename: str) -> str:
        return os.path.join(tempfile.gettempdir(), filename)

    def _revenue_projection_chart(self, context: dict) -> str:
        """5-year revenue vs costs line chart."""
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.ticker as mticker

        pnl_5yr = context.get("financial_model", {}).get("pnl_5yr", [])
        if not pnl_5yr:
            # Generate illustrative data from investment
            investment = context.get("investment_amount_sar", 2_000_000)
            base_rev = investment * 1.5
            pnl_5yr = [
                {
                    "year": i + 1,
                    "revenue": round(base_rev * (1.12**i) * (0.65 if i == 0 else 1)),
                    "cogs": round(
                        base_rev * (1.12**i) * (0.65 if i == 0 else 1) * 0.40
                    ),
                    "opex": round(
                        base_rev * (1.12**i) * (0.65 if i == 0 else 1) * 0.35
                    ),
                    "net_profit": round(
                        base_rev * (1.12**i) * (0.65 if i == 0 else 1) * 0.10
                    ),
                }
                for i in range(5)
            ]

        years = [f"Year {r['year']}" for r in pnl_5yr]
        revenues = [r["revenue"] / 1_000_000 for r in pnl_5yr]
        total_costs = [
            (r.get("cogs", 0) + r.get("opex", 0)) / 1_000_000 for r in pnl_5yr
        ]
        net_profits = [r.get("net_profit", 0) / 1_000_000 for r in pnl_5yr]

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(
            years,
            revenues,
            marker="o",
            linewidth=2.5,
            color="#1B4F72",
            label="Revenue (SAR M)",
        )
        ax.plot(
            years,
            total_costs,
            marker="s",
            linewidth=2.5,
            color="#E74C3C",
            label="Total Costs (SAR M)",
        )
        ax.plot(
            years,
            net_profits,
            marker="^",
            linewidth=2.5,
            color="#27AE60",
            label="Net Profit (SAR M)",
            linestyle="--",
        )
        ax.fill_between(years, net_profits, alpha=0.1, color="#27AE60")

        ax.set_title(
            "5-Year Revenue & Profitability Projection\nتوقعات الإيرادات والربحية لخمس سنوات",
            fontsize=14,
            fontweight="bold",
            pad=15,
        )
        ax.set_xlabel("Year / السنة", fontsize=11)
        ax.set_ylabel("SAR Millions / مليون ريال سعودي", fontsize=11)
        ax.yaxis.set_major_formatter(
            mticker.FuncFormatter(lambda x, _: f"SAR {x:.1f}M")
        )
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.set_facecolor("#FAFAFA")
        fig.patch.set_facecolor("#FFFFFF")
        plt.tight_layout()

        path = self._get_tmp_path("chart_revenue.png")
        plt.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return path

    def _market_size_chart(self, context: dict) -> str:
        """TAM/SAM/SOM funnel bar chart."""
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.ticker as mticker

        market = context.get("market_research", {})
        tam = market.get("tam", {}).get("value_sar", 100_000_000_000)
        sam = market.get("sam", {}).get("value_sar", 15_000_000_000)
        som = market.get("som", {}).get("value_sar", 750_000_000)

        values_bn = [tam / 1e9, sam / 1e9, som / 1e9]
        labels = [
            "TAM\nإجمالي السوق",
            "SAM\nالسوق القابل للخدمة",
            "SOM\nالسوق المستهدف",
        ]
        colors = ["#2E86AB", "#A23B72", "#F18F01"]

        fig, ax = plt.subplots(figsize=(9, 6))
        bars = ax.bar(
            labels, values_bn, color=colors, width=0.5, edgecolor="white", linewidth=1.5
        )

        for bar, val in zip(bars, values_bn):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(values_bn) * 0.01,
                f"SAR {val:.1f}B",
                ha="center",
                va="bottom",
                fontweight="bold",
                fontsize=11,
            )

        ax.set_title(
            "Market Size Analysis — TAM / SAM / SOM\nتحليل حجم السوق",
            fontsize=14,
            fontweight="bold",
            pad=15,
        )
        ax.set_ylabel("SAR Billions / مليار ريال سعودي", fontsize=11)
        ax.yaxis.set_major_formatter(
            mticker.FuncFormatter(lambda x, _: f"SAR {x:.0f}B")
        )
        ax.set_facecolor("#FAFAFA")
        fig.patch.set_facecolor("#FFFFFF")
        ax.grid(axis="y", alpha=0.3)
        plt.tight_layout()

        path = self._get_tmp_path("chart_market.png")
        plt.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return path

    def _risk_matrix_chart(self, context: dict) -> str:
        """Likelihood vs impact scatter plot for risk matrix."""
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches

        risks = context.get("risk_assessment", {}).get("risks", [])
        if not risks:
            risks = [
                {
                    "id": "R001",
                    "category": "market",
                    "likelihood": 3,
                    "impact": 4,
                    "description_en": "Oil price volatility",
                },
                {
                    "id": "R002",
                    "category": "regulatory",
                    "likelihood": 3,
                    "impact": 3,
                    "description_en": "Regulatory changes",
                },
                {
                    "id": "R003",
                    "category": "financial",
                    "likelihood": 2,
                    "impact": 3,
                    "description_en": "Currency risk",
                },
                {
                    "id": "R004",
                    "category": "operational",
                    "likelihood": 4,
                    "impact": 3,
                    "description_en": "Talent shortage",
                },
                {
                    "id": "R005",
                    "category": "market",
                    "likelihood": 4,
                    "impact": 3,
                    "description_en": "Competition",
                },
                {
                    "id": "R006",
                    "category": "financial",
                    "likelihood": 3,
                    "impact": 3,
                    "description_en": "Interest rate risk",
                },
            ]

        category_colors = {
            "market": "#E74C3C",
            "financial": "#F39C12",
            "regulatory": "#8E44AD",
            "operational": "#2980B9",
        }

        fig, ax = plt.subplots(figsize=(10, 8))

        # Heat zone backgrounds
        ax.fill_between([0.5, 2.5], [0.5, 0.5], [5.5, 5.5], alpha=0.08, color="#27AE60")
        ax.fill_between([2.5, 3.5], [0.5, 0.5], [5.5, 5.5], alpha=0.08, color="#F39C12")
        ax.fill_between([3.5, 5.5], [0.5, 0.5], [5.5, 5.5], alpha=0.08, color="#E74C3C")

        for risk in risks:
            cat = risk.get("category", "market")
            color = category_colors.get(cat, "#7F8C8D")
            ax.scatter(
                risk["likelihood"],
                risk["impact"],
                s=180,
                color=color,
                zorder=5,
                edgecolors="white",
                linewidth=1.5,
            )
            ax.annotate(
                risk["id"],
                (risk["likelihood"], risk["impact"]),
                textcoords="offset points",
                xytext=(8, 5),
                fontsize=8,
                color=color,
                fontweight="bold",
            )

        ax.set_xlim(0.5, 5.5)
        ax.set_ylim(0.5, 5.5)
        ax.set_xticks([1, 2, 3, 4, 5])
        ax.set_yticks([1, 2, 3, 4, 5])
        ax.set_xticklabels(
            ["1\nRare", "2\nUnlikely", "3\nPossible", "4\nLikely", "5\nAlmost Certain"],
            fontsize=9,
        )
        ax.set_yticklabels(
            ["1\nNegligible", "2\nMinor", "3\nModerate", "4\nMajor", "5\nCatastrophic"],
            fontsize=9,
        )
        ax.set_xlabel("Likelihood / الاحتمالية", fontsize=11)
        ax.set_ylabel("Impact / الأثر", fontsize=11)
        ax.set_title(
            "Risk Matrix — Likelihood vs. Impact\nمصفوفة المخاطر",
            fontsize=14,
            fontweight="bold",
            pad=15,
        )
        ax.grid(True, alpha=0.2)
        ax.set_facecolor("#FAFAFA")
        fig.patch.set_facecolor("#FFFFFF")

        legend_patches = [
            mpatches.Patch(color=c, label=cat.title())
            for cat, c in category_colors.items()
        ]
        ax.legend(handles=legend_patches, loc="upper left", fontsize=9)
        plt.tight_layout()

        path = self._get_tmp_path("chart_risk.png")
        plt.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return path

    def _nitaqat_chart(self, context: dict) -> str:
        """Saudi vs expat headcount stacked bar chart."""
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        hr_data = context.get("hr_saudization", {})
        staffing = hr_data.get("staffing_plan", [])

        if staffing:
            saudi_count = sum(r.get("count", 1) for r in staffing if r.get("is_saudi"))
            expat_count = sum(
                r.get("count", 1) for r in staffing if not r.get("is_saudi")
            )
            total = saudi_count + expat_count
            nitaqat_pct = round(saudi_count / total * 100, 1) if total else 0
            nitaqat_band = hr_data.get("nitaqat_band", "low_green")
        else:
            saudi_count, expat_count, total = 8, 4, 12
            nitaqat_pct, nitaqat_band = 66.7, "platinum"

        # Stacked horizontal bar
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.barh(
            ["Workforce\nالقوى العاملة"],
            [saudi_count],
            color="#1B4F72",
            label=f"Saudi ({saudi_count})",
            height=0.4,
        )
        ax.barh(
            ["Workforce\nالقوى العاملة"],
            [expat_count],
            left=[saudi_count],
            color="#AED6F1",
            label=f"Expat ({expat_count})",
            height=0.4,
        )

        band_colors = {
            "platinum": "#7D3C98",
            "high_green": "#1E8449",
            "low_green": "#27AE60",
            "yellow": "#F39C12",
            "red": "#E74C3C",
        }
        band_color = band_colors.get(nitaqat_band, "#95A5A6")

        ax.text(
            saudi_count / 2,
            0,
            f"{saudi_count}\nSaudi",
            ha="center",
            va="center",
            color="white",
            fontweight="bold",
            fontsize=12,
        )
        ax.text(
            saudi_count + expat_count / 2,
            0,
            f"{expat_count}\nExpat",
            ha="center",
            va="center",
            color="#1B4F72",
            fontweight="bold",
            fontsize=12,
        )

        band_label = nitaqat_band.replace("_", " ").title()
        ax.set_title(
            f"Nitaqat (نطاقات) Saudization — {nitaqat_pct}% Saudi\nBand: {band_label}",
            fontsize=13,
            fontweight="bold",
            color=band_color,
            pad=12,
        )
        ax.set_xlim(0, total + 1)
        ax.set_xlabel("Number of Employees / عدد الموظفين", fontsize=11)
        ax.legend(loc="lower right", fontsize=10)
        ax.axvline(
            x=total * 0.40,
            color="#E74C3C",
            linestyle="--",
            alpha=0.6,
            label="Min Saudization 40%",
        )
        ax.set_facecolor("#FAFAFA")
        fig.patch.set_facecolor("#FFFFFF")
        ax.grid(axis="x", alpha=0.3)
        plt.tight_layout()

        path = self._get_tmp_path("chart_nitaqat.png")
        plt.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return path
