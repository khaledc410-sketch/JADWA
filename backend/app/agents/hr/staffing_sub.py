"""
StaffingSubAgent -- staffing plans, salary benchmarks, and GOSI cost calculations
for Saudi businesses.
"""

from typing import Any

from app.agents.base_agent import BaseAgent
from app.services.data_tools import get_salary_benchmarks, get_gosi_rates

# Fallback GOSI contribution rates (2024)
_GOSI_EMPLOYER_SAUDI = 0.1175  # 9% pension + 2% unemployment + 0.75% SANED
_GOSI_EMPLOYEE_SAUDI = 0.1000
_GOSI_EMPLOYER_EXPAT = 0.02  # 2% work injury insurance only
_GOSI_EMPLOYEE_EXPAT = 0.00

# Fallback salary benchmarks by role (monthly SAR, mid-range 2024)
_FALLBACK_SALARIES = {
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

# Sector-specific staffing templates
_SECTOR_PLANS = {
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
    "fnb": [
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


class StaffingSubAgent(BaseAgent):
    name: str = "StaffingSubAgent"
    description: str = (
        "Staffing plans, salary benchmarks, and GOSI cost calculations "
        "for Saudi businesses"
    )
    max_tokens: int = 4096
    temperature: float = 0.2

    @property
    def system_prompt(self) -> str:
        return (
            "أنت متخصص في تخطيط القوى العاملة والتعويضات في سوق العمل السعودي.\n\n"
            "You are a Saudi HR staffing and compensation specialist.\n\n"
            "Your responsibilities:\n"
            "- Build realistic staffing plans with Saudi/expat split by role.\n"
            "- Use current Saudi market salary benchmarks.\n"
            "- Calculate GOSI employer and employee contributions.\n"
            "- Provide Arabic and English role names.\n"
            "- All monetary values in SAR.\n"
            "- Return a JSON object with: staffing_plan, total_headcount, "
            "saudi_count, total_monthly_payroll_sar, gosi_summary.\n"
            "  No text outside the JSON block."
        )

    @property
    def tools(self) -> list:
        return [
            {
                "name": "build_staffing_plan",
                "description": (
                    "Builds a recommended staffing plan for the sector and investment "
                    "size, including roles, headcount, Saudi/expat split, salary "
                    "benchmarks, and GOSI costs per role."
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
                    "Calculates GOSI employer and employee contributions "
                    "for a given staffing plan breakdown."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "staffing_plan": {
                            "type": "array",
                            "items": {"type": "object"},
                            "description": (
                                "List of staff entries with is_saudi, "
                                "monthly_salary_sar, and count fields"
                            ),
                        },
                    },
                    "required": ["staffing_plan"],
                },
            },
        ]

    def execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        if tool_name == "build_staffing_plan":
            return self._build_staffing_plan(**tool_input)
        if tool_name == "estimate_gosi_contributions":
            return self._estimate_gosi_contributions(**tool_input)
        raise NotImplementedError(f"Unknown tool: {tool_name}")

    def _get_gosi_rates_safe(self) -> dict:
        """Load GOSI rates from seed data with fallbacks."""
        rates = get_gosi_rates()
        return {
            "employer_saudi": rates.get("employer_saudi", _GOSI_EMPLOYER_SAUDI),
            "employee_saudi": rates.get("employee_saudi", _GOSI_EMPLOYEE_SAUDI),
            "employer_expat": rates.get("employer_expat", _GOSI_EMPLOYER_EXPAT),
            "employee_expat": rates.get("employee_expat", _GOSI_EMPLOYEE_EXPAT),
        }

    def _get_salary_benchmarks_safe(self) -> dict:
        """Load salary benchmarks from seed data with fallbacks."""
        benchmarks = get_salary_benchmarks()
        if benchmarks:
            return benchmarks
        return _FALLBACK_SALARIES

    def _build_staffing_plan(
        self, sector: str, investment_sar: float, city: str = "riyadh"
    ) -> list:
        salaries = self._get_salary_benchmarks_safe()
        gosi = self._get_gosi_rates_safe()

        plan_template = _SECTOR_PLANS.get(sector.lower(), _SECTOR_PLANS["default"])
        plan = []
        for role in plan_template:
            salary_data = salaries.get(role["key"], {"saudi": 6_000, "expat": 4_000})
            nat = "saudi" if role["is_saudi"] else "expat"
            salary = salary_data.get(nat, salary_data.get("saudi", 6_000))
            er_rate = (
                gosi["employer_saudi"] if role["is_saudi"] else gosi["employer_expat"]
            )
            gosi_cost = round(salary * er_rate)
            plan.append(
                {
                    "role_ar": role["role_ar"],
                    "role_en": role["role_en"],
                    "count": role["count"],
                    "is_saudi": role["is_saudi"],
                    "monthly_salary_sar": salary,
                    "gosi_employer_sar": gosi_cost,
                    "total_monthly_cost_sar": round(
                        (salary + gosi_cost) * role["count"]
                    ),
                }
            )
        return plan

    def _estimate_gosi_contributions(self, staffing_plan: list) -> dict:
        gosi = self._get_gosi_rates_safe()
        total_employer = 0
        total_employee = 0

        for emp in staffing_plan:
            salary = emp.get("monthly_salary_sar", 0)
            count = emp.get("count", 1)
            is_saudi = emp.get("is_saudi", True)
            er_rate = gosi["employer_saudi"] if is_saudi else gosi["employer_expat"]
            ee_rate = gosi["employee_saudi"] if is_saudi else gosi["employee_expat"]
            total_employer += salary * er_rate * count
            total_employee += salary * ee_rate * count

        return {
            "monthly_employer_gosi_sar": round(total_employer),
            "monthly_employee_gosi_sar": round(total_employee),
            "annual_employer_gosi_sar": round(total_employer * 12),
            "annual_employee_gosi_sar": round(total_employee * 12),
            "gosi_rates_applied": gosi,
        }

    def _build_user_message(self, context: dict) -> str:
        sector = context.get("sector", "default")
        investment = context.get("investment_amount_sar", 2_000_000)
        city = context.get("city", "Riyadh")
        return (
            f"Build a staffing plan with GOSI costs for this Saudi business.\n"
            f"Sector: {sector} | Investment: SAR {investment:,.0f} | City: {city}\n\n"
            f"Steps:\n"
            f"1. Call build_staffing_plan with sector='{sector}', "
            f"investment_sar={investment}, city='{city}'.\n"
            f"2. Call estimate_gosi_contributions with the resulting staffing plan.\n\n"
            f"Return JSON with: staffing_plan, total_headcount, saudi_count, "
            f"total_monthly_payroll_sar, gosi_summary."
        )
