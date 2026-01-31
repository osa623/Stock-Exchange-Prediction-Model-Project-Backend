import math

# =========================
# CASH FLOW CALCULATIONS
# =========================

def delta_working_capital(wc, years):
    return {
        years[i]: wc[years[i]] - wc[years[i-1]]
        for i in range(1, len(years))
    }

def fcff(ebit, tax, dep, capex, delta_wc):
    return {
        y: ebit[y] * (1 - tax[y]) + dep[y] - capex[y] - delta_wc.get(y, 0)
        for y in ebit
    }

def fcfe(net_income, dep, capex, delta_wc, net_borrowing):
    return {
        y: net_income[y] + dep[y] - capex[y] - delta_wc.get(y, 0) + net_borrowing[y]
        for y in net_income
    }

# =========================
# DCF CORE
# =========================

def terminal_value(fcff_last, wacc, g):
    return fcff_last * (1 + g) / (wacc - g)

def present_value(cashflows, rate):
    return sum(cf / ((1 + rate) ** t) for t, cf in enumerate(cashflows, start=1))

def firm_value(fcffs, wacc, g):
    years = sorted(fcffs)
    pv = present_value([fcffs[y] for y in years], wacc)
    tv = terminal_value(fcffs[years[-1]], wacc, g)
    return pv + tv / ((1 + wacc) ** len(years))


# Compatibility wrappers expected by main.py
def calc_fcff(ebit, tax_rate, depreciation, capex, delta_wc):
    return ebit * (1 - tax_rate) + depreciation - capex - delta_wc


def dcf_firm_value(fcff_value, wacc, g):
    if isinstance(fcff_value, dict):
        return firm_value(fcff_value, wacc, g)
    pv_first = fcff_value / (1 + wacc)
    tv = terminal_value(fcff_value, wacc, g)
    return pv_first + tv / (1 + wacc)

def equity_value_from_firm(firm_value, net_debt):
    return firm_value - net_debt

def intrinsic_price(equity_value, shares):
    return equity_value / shares

# =========================
# OTHER VALUATION MODELS
# =========================

def ddm_gordon(dividend_next, r, g):
    return dividend_next / (r - g)

def residual_income(net_income, equity, cost_of_equity):
    return net_income - (equity * cost_of_equity)
def earnings_power_value(norm_ebit, tax, wacc, net_debt=None, shares_outstanding=None):
    firm_epv = (norm_ebit * (1 - tax)) / wacc
    if net_debt is None:
        return firm_epv
    equity_value = firm_epv - net_debt
    if shares_outstanding:
        return equity_value / shares_outstanding
    return equity_value


# FCFE compatibility wrappers
def calc_fcfe(net_income, depreciation, capex, delta_wc, net_borrowing):
    return net_income + depreciation - capex - delta_wc + net_borrowing


def fcfe_dcf(fcfe_value, r, g):
    if isinstance(fcfe_value, dict):
        # treat dict similarly to firm_value but using cost of equity
        years = sorted(fcfe_value)
        pv = present_value([fcfe_value[y] for y in years], r)
        tv = terminal_value(fcfe_value[years[-1]], r, g)
        return pv + tv / ((1 + r) ** len(years))
    pv_first = fcfe_value / (1 + r)
    tv = terminal_value(fcfe_value, r, g)
    return pv_first + tv / (1 + r)

def adjusted_nav(fair_assets, liabilities):
    return fair_assets - liabilities

def liquidation_value(liquid_assets, liabilities):
    return liquid_assets - liabilities

def replacement_value(replacement_cost, liabilities):
    return replacement_cost - liabilities

# =========================
# FUTURE & RISK
# =========================

def margin_of_safety(intrinsic, market_price):
    return (intrinsic - market_price) / intrinsic

def safe_buy_price(intrinsic, mos):
    return intrinsic * (1 - mos)

def expected_annual_return(future_value, current_price, years):
    return (future_value / current_price) ** (1 / years) - 1
