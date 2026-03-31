"""
HRSaudizationAgent — calculates Nitaqat (نطاقات) ratios, builds staffing plan,
estimates HRDF subsidies, and computes GOSI contributions.
"""

import json
import math
from typing import Any

from app.agents.base_agent import BaseAgent


# ---------------------------------------------------------------------------
# Saudi HR data cache (realistic mock)
# ---------------------------------------------------------------------------

# Nitaqat (نطاقات) band thresholds by sector for companies with 6-49 employees
# (mid-size bracket). Source: MHRSD 2024.
_NITAQAT_THRESHOLDS = {
    "retail": {"platinum": 0.40, "high_green": 0.35, "low_green": 0.25, "yellow": 0.10},
    "food_beverage": {
        "platinum": 0.35,
        "high_green": 0.28,
        "low_green": 0.20,
        "yellow": 0.08,
    },
    "healthcare": {
        "platinum": 0.55,
        "high_green": 0.45,
        "low_green": 0.35,
        "yellow": 0.20,
    },
    "education": {
        "platinum": 0.60,
        "high_green": 0.50,
        "low_green": 0.40,
        "yellow": 0.25,
    },
    "technology": {
        "platinum": 0.40,
        "high_green": 0.32,
        "low_green": 0.25,
        "yellow": 0.10,
    },
    "real_estate": {
        "platinum": 0.50,
        "high_green": 0.42,
        "low_green": 0.35,
        "yellow": 0.15,
    },
    "franchise": {
        "platinum": 0.40,
        "high_green": 0.33,
        "low_green": 0.25,
        "yellow": 0.10,
    },
    "manufacturing": {
        "platinum": 0.45,
        "high_green": 0.38,
        "low_green": 0.30,
        "yellow": 0.12,
    },
    "logistics": {
        "platinum": 0.45,
        "high_green": 0.38,
        "low_green": 0.35,
        "yellow": 0.15,
    },
    "hospitality": {
        "platinum": 0.45,
        "high_green": 0.38,
        "low_green": 0.35,
        "yellow": 0.15,
    },
    "default": {
        "platinum": 0.40,
        "high_green": 0.33,
        "low_green": 0.25,
        "yellow": 0.10,
    },
}

# Average monthly salaries in SAR by role (Saudi market 2024, mid-range)
_SALARY_BENCHMARKS = {
    "general_manager": {"saudi": 22_000, "expat": 18_000},
    "operations_manager": {"saudi": 15_000, "expat": 12_000},
    "finance_manager": {"saudi": 14_000, "expat": 11_000},
    "hr_manager": {"saudi": 12_000, "expat": 9_000},
    "sales_manager": {"saudi": 12_000, "expat": 9_000},
    "accountant": {"saudi": 7_000, "expat": 5_500},
    "sales_associate": {"saudi": 4_500, "expat": 3_500},
    "cashier": {"saudi": 3_800, "expat": 2_800},
    "customer_service": {"saudi": 5_000, "expat": 3_800},
    "warehouse_staff": {"saudi": 4_000, "expat": 2_800},
    "driver": {"saudi": 4_500, "expat": 3_000},
    "it_specialist": {"saudi": 9_000, "expat": 7_000},
    "marketing_specialist": {"saudi": 8_000, "expat": 6_500},
    "receptionist": {"saudi": 4_500, "expat": 3_000},
    "security": {"saudi": 3_500, "expat": 2_500},
    "cleaner": {"saudi": 2_800, "expat": 1_800},
}

# GOSI (التأمينات الاجتماعية) contribution rates 2024
GOSI_EMPLOYER_SAUDI = (
    0.1175  # 11.75% for Saudi employees (9% pension + 2% unemployment)
)
GOSI_EMPLOYEE_SAUDI = 0.1000  # 10% employee contribution (Saudi)
GOSI_EMPLOYER_EXPAT = 0.02  # 2% work injury insurance only for expats
GOSI_EMPLOYEE_EXPAT = 0.00  # 0% for expats

# HRDF (صندوق تنمية الموارد البشرية) subsidy: 50% of Saudi salary for year 1, max SAR 4,000/month
HRDF_SUBSIDY_RATE = 0.50
HRDF_MAX_MONTHLY_SAR = 4_000


class HRSaudizationAgent(BaseAgent):
    name: str = "HRSaudizationAgent"
    description: str = "Nitaqat compliance, staffing plan, HRDF subsidies, GOSI"
    temperature: float = 0.2

    @property
    def system_prompt(self) -> str:
        return (
            "أنت متخصص في الموارد البشرية والامتثال لنظام نطاقات (السعودة) في المملكة العربية السعودية.\n\n"
            "You are a Saudi HR specialist expert in:\n"
            "- Nitaqat (نطاقات) Saudization compliance and band calculations\n"
            "- HRDF (صندوق تنمية الموارد البشرية) subsidy programs\n"
            "- GOSI (التأمينات الاجتماعية) contribution calculations\n"
            "- Average Saudi market salaries by role and sector\n"
            "- Workforce planning for Saudi SMEs\n\n"
            "Instructions:\n"
            "- Build a realistic staffing plan with Saudi and expat split.\n"
            "- Calculate Nitaqat band (platinum/high_green/low_green/yellow/red).\n"
            "- Compute HRDF subsidies for Year 1.\n"
            "- Include GOSI employer contributions in total labor cost.\n"
            "- Use current Saudi salary benchmarks.\n"
            "- Provide Arabic and English role names.\n"
            "Return a JSON object matching the output schema exactly."
        )

    @property
    def tools(self) -> list:
        return [
            {
                "name": "calculate_nitaqat_ratio",
                "description": (
                    "Calculates the Nitaqat Saudization percentage and determines "
                    "the compliance band (platinum/high_green/low_green/yellow/red) "
                    "for a given sector and headcount."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sector": {"type": "string"},
                        "total_headcount": {"type": "integer"},
                        "saudi_count": {"type": "integer"},
                    },
                    "required": ["sector", "total_headcount", "saudi_count"],
                },
            },
            {
                "name": "fetch_hrdf_subsidies",
                "description": (
                    "Returns available HRDF subsidy programs for new Saudi hires, "
                    "including On-the-Job training subsidy, graduate hiring subsidy, etc."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sector": {"type": "string"},
                        "saudi_headcount": {"type": "integer"},
                        "avg_salary_sar": {"type": "number"},
                    },
                    "required": ["saudi_headcount"],
                },
            },
            {
                "name": "build_staffing_plan",
                "description": (
                    "Builds a recommended staffing plan for the sector and investment size, "
                    "including roles, headcount, Saudi/expat split, and salary benchmarks."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sector": {"type": "string"},
                        "investment_sar": {"type": "number"},
                        "city": {"type": "string"},
                    },
                    "required": ["sector", "investment_sar"],
                },
            },
            {
                "name": "estimate_gosi_contributions",
                "description": (
                    "Calculates GOSI employer and employee contributions for a staffing plan."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "staffing_plan": {
                            "type": "array",
                            "items": {"type": "object"},
                            "description": "List of staff with is_saudi and monthly_salary_sar",
                        },
                    },
                    "required": ["staffing_plan"],
                },
            },
        ]

    # ------------------------------------------------------------------
    # Tool implementations
    # ------------------------------------------------------------------

    def execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        if tool_name == "calculate_nitaqat_ratio":
            return self._calculate_nitaqat_ratio(**tool_input)
        if tool_name == "fetch_hrdf_subsidies":
            return self._fetch_hrdf_subsidies(**tool_input)
        if tool_name == "build_staffing_plan":
            return self._build_staffing_plan(**tool_input)
        if tool_name == "estimate_gosi_contributions":
            return self._estimate_gosi_contributions(**tool_input)
        raise NotImplementedError(f"Unknown tool: {tool_name}")

    def _calculate_nitaqat_ratio(
        self, sector: str, total_headcount: int, saudi_count: int
    ) -> dict:
        pct = saudi_count / total_headcount if total_headcount > 0 else 0
        thresholds = _NITAQAT_THRESHOLDS.get(
            sector.lower(), _NITAQAT_THRESHOLDS["default"]
        )

        if pct >= thresholds["platinum"]:
            band = "platinum"
            band_ar = "البلاتيني"
        elif pct >= thresholds["high_green"]:
            band = "high_green"
            band_ar = "الأخضر المرتفع"
        elif pct >= thresholds["low_green"]:
            band = "low_green"
            band_ar = "الأخضر المنخفض"
        elif pct >= thresholds["yellow"]:
            band = "yellow"
            band_ar = "الأصفر"
        else:
            band = "red"
            band_ar = "الأحمر"

        return {
            "nitaqat_percentage": round(pct * 100, 1),
            "nitaqat_band": band,
            "nitaqat_band_ar": band_ar,
            "saudi_count": saudi_count,
            "total_headcount": total_headcount,
            "expat_count": total_headcount - saudi_count,
            "thresholds": thresholds,
            "compliant": band not in ["yellow", "red"],
            "to_reach_low_green": max(
                0, math.ceil(total_headcount * thresholds["low_green"]) - saudi_count
            ),
            "to_reach_platinum": max(
                0, math.ceil(total_headcount * thresholds["platinum"]) - saudi_count
            ),
        }

    def _fetch_hrdf_subsidies(
        self,
        saudi_headcount: int,
        sector: str = "default",
        avg_salary_sar: float = 6_000,
    ) -> dict:
        monthly_subsidy_per_hire = min(
            avg_salary_sar * HRDF_SUBSIDY_RATE, HRDF_MAX_MONTHLY_SAR
        )
        annual_subsidy = round(monthly_subsidy_per_hire * 12 * saudi_headcount)

        programs = [
            {
                "program_name_en": "HRDF On-the-Job Training Subsidy",
                "program_name_ar": "دعم التدريب على رأس العمل",
                "benefit": f"50% of salary up to SAR {HRDF_MAX_MONTHLY_SAR:,}/month per hire for 12 months",
                "max_duration_months": 12,
                "eligible_headcount": saudi_headcount,
                "estimated_benefit_sar": annual_subsidy,
            },
            {
                "program_name_en": "Saudization Premium (Nitaqat Platinum)",
                "program_name_ar": "مكافأة السعودة - مستوى البلاتيني",
                "benefit": "Priority access to government procurement and reduced CR fees",
                "max_duration_months": 36,
                "eligible_headcount": saudi_headcount,
                "estimated_benefit_sar": 15_000,
            },
            {
                "program_name_en": "HRDF Graduate Hiring Program",
                "program_name_ar": "برنامج توظيف الخريجين",
                "benefit": "SAR 2,000/month subsidy for fresh Saudi graduates (first 2 years)",
                "max_duration_months": 24,
                "eligible_headcount": round(saudi_headcount * 0.3),
                "estimated_benefit_sar": round(saudi_headcount * 0.3 * 2_000 * 12),
            },
        ]

        return {
            "sector": sector,
            "saudi_headcount": saudi_headcount,
            "monthly_subsidy_per_hire_sar": round(monthly_subsidy_per_hire),
            "total_annual_subsidy_sar": annual_subsidy,
            "programs": programs,
        }

    def _build_staffing_plan(
        self, sector: str, investment_sar: float, city: str = "riyadh"
    ) -> list:
        sector_plans = {
            "food_beverage": [
                {
                    "role_en": "Restaurant Manager",
                    "role_ar": "مدير المطعم",
                    "count": 1,
                    "is_saudi": True,
                    "key": "operations_manager",
                },
                {
                    "role_en": "Head Chef",
                    "role_ar": "رئيس الطهاة",
                    "count": 1,
                    "is_saudi": False,
                    "key": "operations_manager",
                },
                {
                    "role_en": "Chef",
                    "role_ar": "طاهٍ",
                    "count": 2,
                    "is_saudi": False,
                    "key": "warehouse_staff",
                },
                {
                    "role_en": "Cashier",
                    "role_ar": "كاشير",
                    "count": 2,
                    "is_saudi": True,
                    "key": "cashier",
                },
                {
                    "role_en": "Service Staff",
                    "role_ar": "طاقم خدمة",
                    "count": 4,
                    "is_saudi": True,
                    "key": "sales_associate",
                },
                {
                    "role_en": "Delivery Driver",
                    "role_ar": "سائق توصيل",
                    "count": 2,
                    "is_saudi": True,
                    "key": "driver",
                },
            ],
            "retail": [
                {
                    "role_en": "Store Manager",
                    "role_ar": "مدير المتجر",
                    "count": 1,
                    "is_saudi": True,
                    "key": "operations_manager",
                },
                {
                    "role_en": "Accountant",
                    "role_ar": "محاسب",
                    "count": 1,
                    "is_saudi": True,
                    "key": "accountant",
                },
                {
                    "role_en": "Sales Associate",
                    "role_ar": "مندوب مبيعات",
                    "count": 4,
                    "is_saudi": True,
                    "key": "sales_associate",
                },
                {
                    "role_en": "Cashier",
                    "role_ar": "كاشير",
                    "count": 2,
                    "is_saudi": True,
                    "key": "cashier",
                },
                {
                    "role_en": "Warehouse Staff",
                    "role_ar": "موظف مستودع",
                    "count": 2,
                    "is_saudi": False,
                    "key": "warehouse_staff",
                },
                {
                    "role_en": "Security",
                    "role_ar": "حارس أمن",
                    "count": 1,
                    "is_saudi": False,
                    "key": "security",
                },
            ],
            "technology": [
                {
                    "role_en": "General Manager",
                    "role_ar": "المدير العام",
                    "count": 1,
                    "is_saudi": True,
                    "key": "general_manager",
                },
                {
                    "role_en": "Software Engineer",
                    "role_ar": "مهندس برمجيات",
                    "count": 3,
                    "is_saudi": True,
                    "key": "it_specialist",
                },
                {
                    "role_en": "Product Manager",
                    "role_ar": "مدير المنتج",
                    "count": 1,
                    "is_saudi": True,
                    "key": "it_specialist",
                },
                {
                    "role_en": "Marketing Specialist",
                    "role_ar": "متخصص تسويق",
                    "count": 1,
                    "is_saudi": True,
                    "key": "marketing_specialist",
                },
                {
                    "role_en": "Finance Manager",
                    "role_ar": "مدير مالي",
                    "count": 1,
                    "is_saudi": True,
                    "key": "finance_manager",
                },
                {
                    "role_en": "Customer Support",
                    "role_ar": "دعم العملاء",
                    "count": 2,
                    "is_saudi": True,
                    "key": "customer_service",
                },
            ],
            "default": [
                {
                    "role_en": "General Manager",
                    "role_ar": "المدير العام",
                    "count": 1,
                    "is_saudi": True,
                    "key": "general_manager",
                },
                {
                    "role_en": "Operations Manager",
                    "role_ar": "مدير العمليات",
                    "count": 1,
                    "is_saudi": True,
                    "key": "operations_manager",
                },
                {
                    "role_en": "Accountant",
                    "role_ar": "محاسب",
                    "count": 1,
                    "is_saudi": True,
                    "key": "accountant",
                },
                {
                    "role_en": "Sales Associate",
                    "role_ar": "مندوب مبيعات",
                    "count": 3,
                    "is_saudi": True,
                    "key": "sales_associate",
                },
                {
                    "role_en": "Customer Service",
                    "role_ar": "خدمة عملاء",
                    "count": 2,
                    "is_saudi": True,
                    "key": "customer_service",
                },
                {
                    "role_en": "Driver/Delivery",
                    "role_ar": "سائق / توصيل",
                    "count": 2,
                    "is_saudi": False,
                    "key": "driver",
                },
            ],
        }
        plan_template = sector_plans.get(sector.lower(), sector_plans["default"])
        plan = []
        for role in plan_template:
            salary_key = _SALARY_BENCHMARKS.get(
                role["key"], {"saudi": 6_000, "expat": 4_000}
            )
            nat = "saudi" if role["is_saudi"] else "expat"
            salary = salary_key[nat]
            gosi = round(
                salary
                * (GOSI_EMPLOYER_SAUDI if role["is_saudi"] else GOSI_EMPLOYER_EXPAT)
            )
            plan.append(
                {
                    "role_ar": role["role_ar"],
                    "role_en": role["role_en"],
                    "count": role["count"],
                    "is_saudi": role["is_saudi"],
                    "monthly_salary_sar": salary,
                    "gosi_employer_sar": gosi,
                    "total_monthly_cost_sar": round((salary + gosi) * role["count"]),
                }
            )
        return plan

    def _estimate_gosi_contributions(self, staffing_plan: list) -> dict:
        total_employer = 0
        total_employee = 0
        for emp in staffing_plan:
            salary = emp.get("monthly_salary_sar", 0)
            count = emp.get("count", 1)
            is_saudi = emp.get("is_saudi", True)
            er_rate = GOSI_EMPLOYER_SAUDI if is_saudi else GOSI_EMPLOYER_EXPAT
            ee_rate = GOSI_EMPLOYEE_SAUDI if is_saudi else GOSI_EMPLOYEE_EXPAT
            total_employer += salary * er_rate * count
            total_employee += salary * ee_rate * count

        return {
            "monthly_employer_gosi_sar": round(total_employer),
            "monthly_employee_gosi_sar": round(total_employee),
            "annual_employer_gosi_sar": round(total_employer * 12),
            "annual_employee_gosi_sar": round(total_employee * 12),
            "gosi_employer_rate_saudi": GOSI_EMPLOYER_SAUDI,
            "gosi_employer_rate_expat": GOSI_EMPLOYER_EXPAT,
        }

    def _build_user_message(self, context: dict) -> str:
        sector = context.get("sector", "default")
        investment = context.get("investment_amount_sar", 2_000_000)
        city = context.get("city", "Riyadh")
        return (
            f"Build a comprehensive HR and Saudization plan for this Saudi business.\n"
            f"Sector: {sector} | Investment: SAR {investment:,.0f} | City: {city}\n\n"
            f"Steps:\n"
            f"1. Call build_staffing_plan to get recommended roles and headcount.\n"
            f"2. Call calculate_nitaqat_ratio using total and Saudi headcount from the plan.\n"
            f"3. Call fetch_hrdf_subsidies for Year 1 subsidy estimates.\n"
            f"4. Call estimate_gosi_contributions for the full staffing plan.\n\n"
            f"Return JSON: staffing_plan, total_headcount, saudi_count, nitaqat_percentage, "
            f"nitaqat_band, hrdf_subsidy_year1_sar, total_annual_labor_cost_sar, "
            f"narrative_ar, narrative_en.\n\n"
            f"Full context:\n{json.dumps(context, ensure_ascii=False, indent=2)}"
        )
