"""
Pure-Python financial calculator engine.
No external API calls — takes assumptions dict and returns recalculated financials.
Targets < 100ms execution time.
"""

from typing import Dict, List, Optional, Tuple, Union
import math


def calculate_pnl(assumptions: Dict) -> Dict:
    """Calculate 5-year P&L from assumptions.

    Input assumptions dict:
    - monthly_revenue: float (SAR)
    - revenue_growth_rate: float (annual, e.g. 0.15 for 15%)
    - cogs_percent: float (e.g. 0.35 for 35%)
    - monthly_rent: float (SAR)
    - monthly_salaries: float (SAR)
    - headcount: int
    - salary_growth_rate: float (annual)
    - marketing_percent: float (of revenue)
    - utilities_monthly: float (SAR)
    - other_opex_monthly: float (SAR)
    - depreciation_annual: float (SAR)
    - vat_rate: float (default 0.15)
    - zakat_rate: float (default 0.025)

    Returns dict with key 'years': list of 5 year dicts.
    """
    monthly_revenue = float(assumptions.get("monthly_revenue", 0))
    revenue_growth = float(assumptions.get("revenue_growth_rate", 0.0))
    cogs_pct = float(assumptions.get("cogs_percent", 0.0))
    monthly_rent = float(assumptions.get("monthly_rent", 0))
    monthly_salaries = float(assumptions.get("monthly_salaries", 0))
    headcount = int(assumptions.get("headcount", 1))
    salary_growth = float(assumptions.get("salary_growth_rate", 0.0))
    marketing_pct = float(assumptions.get("marketing_percent", 0.0))
    utilities = float(assumptions.get("utilities_monthly", 0))
    other_opex = float(assumptions.get("other_opex_monthly", 0))
    depreciation = float(assumptions.get("depreciation_annual", 0))
    zakat_rate = float(assumptions.get("zakat_rate", 0.025))

    years = []  # type: List[Dict]
    for yr in range(1, 6):
        # Revenue grows annually; year 1 uses the base monthly_revenue
        annual_revenue = monthly_revenue * 12 * ((1 + revenue_growth) ** (yr - 1))

        cogs = annual_revenue * cogs_pct
        gross_profit = annual_revenue - cogs
        gross_margin = (gross_profit / annual_revenue) if annual_revenue else 0.0

        # Salaries grow each year; headcount stays constant in the simple model
        annual_salaries = (
            monthly_salaries * headcount * 12 * ((1 + salary_growth) ** (yr - 1))
        )
        annual_rent = monthly_rent * 12
        marketing = annual_revenue * marketing_pct
        annual_utilities = utilities * 12
        annual_other_opex = other_opex * 12

        total_opex = (
            annual_rent
            + annual_salaries
            + marketing
            + annual_utilities
            + annual_other_opex
        )

        ebitda = gross_profit - total_opex
        ebitda_margin = (ebitda / annual_revenue) if annual_revenue else 0.0

        ebit = ebitda - depreciation

        # Zakat is applied on adjusted net income (simplified)
        zakat = max(0, ebit * zakat_rate) if ebit > 0 else 0.0

        net_income = ebit - zakat
        net_margin = (net_income / annual_revenue) if annual_revenue else 0.0

        years.append(
            {
                "year": yr,
                "revenue": round(annual_revenue, 2),
                "cogs": round(cogs, 2),
                "gross_profit": round(gross_profit, 2),
                "gross_margin": round(gross_margin, 4),
                "rent": round(annual_rent, 2),
                "salaries": round(annual_salaries, 2),
                "marketing": round(marketing, 2),
                "utilities": round(annual_utilities, 2),
                "other_opex": round(annual_other_opex, 2),
                "total_opex": round(total_opex, 2),
                "ebitda": round(ebitda, 2),
                "ebitda_margin": round(ebitda_margin, 4),
                "depreciation": round(depreciation, 2),
                "ebit": round(ebit, 2),
                "zakat": round(zakat, 2),
                "net_income": round(net_income, 2),
                "net_margin": round(net_margin, 4),
            }
        )

    return {"years": years}


def calculate_irr(
    cash_flows: List[float], max_iter: int = 200, tol: float = 1e-8
) -> float:
    """Calculate Internal Rate of Return using Newton's method.

    cash_flows[0] is initial investment (negative), rest are annual net cash flows.
    Returns IRR as decimal (e.g. 0.25 for 25%).
    Returns 0.0 if convergence fails or inputs are invalid.
    """
    if not cash_flows or len(cash_flows) < 2:
        return 0.0

    # Initial guess
    total_positive = sum(cf for cf in cash_flows[1:] if cf > 0)
    if total_positive == 0:
        return 0.0
    rate = 0.1  # 10% initial guess

    for _ in range(max_iter):
        npv_val = 0.0
        d_npv = 0.0
        for t, cf in enumerate(cash_flows):
            denom = (1 + rate) ** t
            if denom == 0:
                return 0.0
            npv_val += cf / denom
            if t > 0:
                d_npv -= t * cf / ((1 + rate) ** (t + 1))

        if abs(d_npv) < 1e-14:
            break

        new_rate = rate - npv_val / d_npv

        # Guard against divergence
        if new_rate < -0.99:
            new_rate = -0.99
        if new_rate > 10.0:
            new_rate = 10.0

        if abs(new_rate - rate) < tol:
            return round(new_rate, 6)

        rate = new_rate

    return round(rate, 6)


def calculate_npv(cash_flows: List[float], discount_rate: float) -> float:
    """Calculate Net Present Value.

    discount_rate as decimal (e.g. 0.10 for 10%).
    """
    if not cash_flows:
        return 0.0
    npv = 0.0
    for t, cf in enumerate(cash_flows):
        npv += cf / ((1 + discount_rate) ** t)
    return round(npv, 2)


def calculate_payback(
    initial_investment: float, annual_cash_flows: List[float]
) -> float:
    """Calculate payback period in months.

    Returns number of months to recover the initial investment.
    If never recovered, returns -1.
    """
    if initial_investment <= 0:
        return 0.0
    if not annual_cash_flows:
        return -1.0

    cumulative = 0.0
    for year_idx, annual_cf in enumerate(annual_cash_flows):
        monthly_cf = annual_cf / 12.0
        for month in range(12):
            cumulative += monthly_cf
            if cumulative >= initial_investment:
                total_months = year_idx * 12 + month + 1
                return float(total_months)

    return -1.0


def calculate_break_even(
    fixed_costs_monthly: float,
    unit_price: float,
    unit_variable_cost: float,
) -> Dict:
    """Calculate break-even point.

    Returns dict with:
    - units_per_month: number of units needed to break even
    - revenue_per_month: SAR revenue at break-even
    - months_to_break_even: estimated months to reach break-even volume
      (assumes linear ramp from 0 to break-even units over time)
    """
    contribution_margin = unit_price - unit_variable_cost
    if contribution_margin <= 0:
        return {
            "units_per_month": -1,
            "revenue_per_month": -1,
            "months_to_break_even": -1,
        }

    be_units = math.ceil(fixed_costs_monthly / contribution_margin)
    be_revenue = round(be_units * unit_price, 2)

    # Estimate months to reach break-even assuming a linear ramp-up:
    # month 1 sells 1 unit, month 2 sells 2 units ... month N sells N units
    # cumulative units at month N = N*(N+1)/2 >= be_units
    # solve N^2 + N - 2*be_units = 0
    discriminant = 1 + 8 * be_units
    months = math.ceil((-1 + math.sqrt(discriminant)) / 2)

    return {
        "units_per_month": be_units,
        "revenue_per_month": be_revenue,
        "months_to_break_even": months,
    }


def _compute_verdict(
    irr: float,
    payback_months: float,
    avg_net_margin: float,
) -> Dict:
    """Compute feasibility verdict from financial metrics."""

    # Determine color/recommendation
    if irr > 0.20 and 0 < payback_months < 36:
        verdict_color = "green"
        verdict_ar = "موصى به"  # RECOMMENDED
    elif irr > 0.10 or (0 < payback_months < 48):
        verdict_color = "yellow"
        verdict_ar = "مشروط"  # CONDITIONAL
    else:
        verdict_color = "red"
        verdict_ar = "غير موصى به"  # NOT RECOMMENDED

    # Feasibility score: weighted formula
    # IRR component (40%): cap at 50% IRR for scoring
    irr_score = min(irr / 0.50, 1.0) * 100 if irr > 0 else 0
    # Payback component (30%): best = 12 months, worst = 60+ months
    if payback_months <= 0 or payback_months > 60:
        payback_score = 0
    else:
        payback_score = max(0, (60 - payback_months) / 48 * 100)
    # Net margin component (30%): cap at 30% margin
    margin_score = min(max(avg_net_margin, 0) / 0.30, 1.0) * 100

    feasibility_score = round(
        irr_score * 0.40 + payback_score * 0.30 + margin_score * 0.30, 1
    )

    return {
        "feasibility_score": feasibility_score,
        "verdict_color": verdict_color,
        "verdict_ar": verdict_ar,
        "irr_score": round(irr_score, 1),
        "payback_score": round(payback_score, 1),
        "margin_score": round(margin_score, 1),
    }


def recalculate_scenario(original_assumptions: Dict, overrides: Dict) -> Dict:
    """Apply overrides to original assumptions and recalculate everything.

    Returns dict with:
    - assumptions: merged dict
    - pnl: 5-year P&L
    - irr: float
    - npv: float (at 10% discount rate)
    - payback_months: float
    - break_even: dict
    - verdict_update: dict with feasibility_score, verdict_color, verdict_ar
    """
    # 1. Merge assumptions
    merged = dict(original_assumptions)
    merged.update(overrides)

    # 2. Calculate 5-year P&L
    pnl = calculate_pnl(merged)
    years = pnl["years"]

    # 3. Build cash flows for IRR/NPV
    initial_investment = float(merged.get("initial_investment", 0))
    if initial_investment == 0:
        # Estimate from first-year opex + depreciation if not given
        initial_investment = years[0]["total_opex"] + years[0]["depreciation"]

    # Year 0 = negative investment, years 1-5 = net_income + depreciation (free cash flow proxy)
    cash_flows = [-abs(initial_investment)]
    for yr_data in years:
        annual_fcf = yr_data["net_income"] + yr_data["depreciation"]
        cash_flows.append(annual_fcf)

    # 4. Calculate IRR, NPV, payback
    irr = calculate_irr(cash_flows)
    npv = calculate_npv(cash_flows, 0.10)
    payback = calculate_payback(
        abs(initial_investment),
        [yr["net_income"] + yr["depreciation"] for yr in years],
    )

    # 5. Break-even (use unit economics if provided, otherwise estimate)
    unit_price = float(merged.get("unit_price", 0))
    unit_variable_cost = float(merged.get("unit_variable_cost", 0))
    fixed_costs_monthly = float(merged.get("fixed_costs_monthly", 0))

    if fixed_costs_monthly == 0:
        # Estimate from year-1 opex
        fixed_costs_monthly = years[0]["total_opex"] / 12.0

    if unit_price > 0 and unit_variable_cost >= 0:
        break_even = calculate_break_even(
            fixed_costs_monthly, unit_price, unit_variable_cost
        )
    else:
        break_even = {
            "units_per_month": -1,
            "revenue_per_month": -1,
            "months_to_break_even": -1,
        }

    # 6. Verdict
    avg_net_margin = (
        sum(yr["net_margin"] for yr in years) / len(years) if years else 0.0
    )
    verdict_update = _compute_verdict(irr, payback, avg_net_margin)

    return {
        "assumptions": merged,
        "pnl": pnl,
        "irr": irr,
        "npv": npv,
        "payback_months": payback,
        "break_even": break_even,
        "verdict_update": verdict_update,
    }
