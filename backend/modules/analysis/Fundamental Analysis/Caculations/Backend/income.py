# =====================================================
# LOAD COMPANY DATA
# =====================================================
def load_data(path):
    data = {}
    with open(path, "r", encoding="utf-8") as f:
        exec(f.read(), {}, data)
    return data


# =====================================================
# DERIVED INCOME STATEMENT CALCULATIONS
# =====================================================
def revenue_growth(revenue, years):
    growth = {}
    for i in range(1, len(years)):
        y0, y1 = years[i-1], years[i]
        growth[y1] = (revenue[y1] - revenue[y0]) / revenue[y0]
    return growth


def gross_profit(revenue, cogs):
    return {y: revenue[y] - cogs[y] for y in revenue}


def gross_margin(gp, revenue):
    return {y: gp[y] / revenue[y] for y in gp}


def operating_profit(gp, rd, sga):
    return {y: gp[y] - rd[y] - sga[y] for y in gp}


def operating_margin(op, revenue):
    return {y: op[y] / revenue[y] for y in op}


def ebitda(op, dep, amort):
    return {y: op[y] + dep[y] + amort[y] for y in op}


def ebitda_margin(ebitda, revenue):
    return {y: ebitda[y] / revenue[y] for y in ebitda}


def net_margin(net_income, revenue):
    return {y: net_income[y] / revenue[y] for y in net_income}


def effective_tax_rate(tax, op):
    return {y: tax[y] / op[y] if op[y] != 0 else None for y in tax}


def interest_coverage(op, interest):
    return {y: op[y] / interest[y] if interest[y] != 0 else None for y in op}


def earnings_quality_accrual(net_income, cfo):
    return {y: (net_income[y] - cfo[y]) / net_income[y] if net_income[y] != 0 else None for y in net_income}


def operating_expense_ratio(rd, sga, revenue):
    return {y: (rd[y] + sga[y]) / revenue[y] for y in revenue}


def cost_structure(cogs, rd, sga, revenue):
    return {
        "COGS %": {y: cogs[y] / revenue[y] for y in revenue},
        "R&D %": {y: rd[y] / revenue[y] for y in revenue},
        "SG&A %": {y: sga[y] / revenue[y] for y in revenue},
    }


# =====================================================
# ADVANCED INCOME STATEMENT CALCULATIONS
# =====================================================

def operating_leverage(ebit, revenue, years):
    ol = {}
    for i in range(1, len(years)):
        y0, y1 = years[i-1], years[i]
        ebit_growth = (ebit[y1] - ebit[y0]) / abs(ebit[y0])
        rev_growth = (revenue[y1] - revenue[y0]) / revenue[y0]
        ol[y1] = ebit_growth / rev_growth if rev_growth != 0 else None
    return ol

def contribution_margin(revenue, cogs):
    return {y: (revenue[y] - cogs[y]) / revenue[y] for y in revenue}

def break_even_revenue(rd, sga, contribution_margin):
    return {
        y: (rd[y] + sga[y]) / contribution_margin[y]
        if contribution_margin[y] != 0 else None
        for y in contribution_margin
    }

def earnings_growth(net_income, years):
    growth = {}
    for i in range(1, len(years)):
        y0, y1 = years[i-1], years[i]
        growth[y1] = (net_income[y1] - net_income[y0]) / net_income[y0]
    return growth

def ebit_vs_revenue_growth(ebit, revenue, years):
    diff = {}
    for i in range(1, len(years)):
        y0, y1 = years[i-1], years[i]
        ebit_g = (ebit[y1] - ebit[y0]) / abs(ebit[y0])
        rev_g = (revenue[y1] - revenue[y0]) / revenue[y0]
        diff[y1] = ebit_g - rev_g
    return diff

def expense_elasticity(rd, sga, revenue, years):
    elasticity = {}
    for i in range(1, len(years)):
        y0, y1 = years[i-1], years[i]
        exp0 = rd[y0] + sga[y0]
        exp1 = rd[y1] + sga[y1]
        exp_growth = (exp1 - exp0) / exp0
        rev_growth = (revenue[y1] - revenue[y0]) / revenue[y0]
        elasticity[y1] = exp_growth / rev_growth if rev_growth != 0 else None
    return elasticity

def core_earnings(ebit, tax_rate):
    return {y: ebit[y] * (1 - (tax_rate.get(y) or 0)) for y in ebit}

def normalized_earnings(net_income):
    avg = sum(net_income.values()) / len(net_income)
    return avg

import statistics

def earnings_volatility(earnings_growth):
    values = [v for v in earnings_growth.values() if v is not None]
    return statistics.stdev(values) if len(values) > 1 else 0

def operating_margin_trend(op_margin, years):
    trend = {}
    for i in range(1, len(years)):
        y0, y1 = years[i-1], years[i]
        trend[y1] = op_margin[y1] - op_margin[y0]
    return trend

def pricing_power_indicator(gross_margin):
    vals = [v for v in gross_margin.values() if v is not None]
    return sum(vals) / len(vals) if vals else 0


def cost_inflation_absorption(gross_margin, years):
    absorption = {}
    for i in range(1, len(years)):
        y0, y1 = years[i-1], years[i]
        gm0 = gross_margin.get(y0)
        gm1 = gross_margin.get(y1)
        absorption[y1] = (gm1 - gm0) if (gm0 is not None and gm1 is not None) else None
    return absorption

def earnings_quality_score(accrual, volatility, margin_trend):
    score = 100
    score -= abs(sum(accrual.values()) / len(accrual)) * 100
    score -= volatility * 100
    score -= abs(sum(margin_trend.values())) * 50
    return max(0, round(score, 2))


def incremental_margin(op, revenue, years):
    inc = {}
    for i in range(1, len(years)):
        y0, y1 = years[i-1], years[i]
        inc[y1] = (op[y1] - op[y0]) / (revenue[y1] - revenue[y0])
    return inc

def incremental_ebitda_margin(ebitda, revenue, years):
    inc = {}
    for i in range(1, len(years)):
        y0, y1 = years[i-1], years[i]
        inc[y1] = (ebitda[y1] - ebitda[y0]) / (revenue[y1] - revenue[y0])
    return inc


def recurring_earnings_ratio(net_income, one_off_items):
    return {
        y: (net_income[y] - one_off_items.get(y, 0)) / net_income[y]
        if net_income[y] != 0 else None
        for y in net_income
    }

def profit_conversion_ratio(net_income, cfo):
    return {
        y: cfo[y] / net_income[y] if net_income[y] != 0 else None
        for y in net_income
    }

def depreciation_intensity(dep, revenue):
    return {y: dep[y] / revenue[y] for y in revenue}


def earnings_sensitivity_to_costs(cogs, revenue, years):
    sensitivity = {}
    for i in range(1, len(years)):
        y0, y1 = years[i-1], years[i]
        cost_growth = (cogs[y1] - cogs[y0]) / cogs[y0]
        rev_growth = (revenue[y1] - revenue[y0]) / revenue[y0]
        sensitivity[y1] = cost_growth - rev_growth
    return sensitivity

def operating_safety_margin(op, revenue):
    return {y: op[y] / revenue[y] for y in revenue}

def fixed_cost_coverage(ebitda, fixed_costs):
    return {
        y: ebitda[y] / fixed_costs[y] if fixed_costs[y] != 0 else None
        for y in ebitda
    }


def growth_persistence_index(revenue_growth):
    vals = [v for v in revenue_growth.values() if v is not None]
    return sum(vals) / len(vals) if vals else 0

def margin_stability_score(op_margin):
    import statistics
    vals = list(op_margin.values())
    return 1 / statistics.stdev(vals) if len(vals) > 1 else 0


def earnings_power(ebit, tax_rate):
    return {
        y: ebit[y] * (1 - (tax_rate.get(y) or 0))
        for y in ebit
    }

def pre_tax_return_proxy(ebit, revenue):
    return {y: ebit[y] / revenue[y] for y in revenue}

