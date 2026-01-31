# =====================================================
# MARKET / VALUATION RATIOS
# =====================================================

def market_cap(price, shares):
    return price * shares

def pe_ratio(price, eps):
    return price / eps if eps != 0 else None

def pb_ratio(price, bvps):
    return price / bvps if bvps != 0 else None

def ps_ratio(price, revenue, shares):
    return price / (revenue / shares)

def earnings_yield(eps, price):
    return eps / price if price != 0 else None

def enterprise_value(market_cap, debt, cash):
    return market_cap + debt - cash

def ev_ebitda(ev, ebitda):
    return ev / ebitda if ebitda != 0 else None

def ev_ebit(ev, ebit):
    return ev / ebit if ebit != 0 else None

def ev_sales(ev, revenue):
    return ev / revenue


# =====================================================
# PER SHARE
# =====================================================

def eps(net_income, shares):
    return net_income / shares

def bvps(equity, shares):
    return equity / shares



# =====================================================
# RETURN RATIOS (CROSS-STATEMENT)
# =====================================================

def roe(net_income, equity):
    return net_income / equity if equity != 0 else None

def roa(net_income, assets):
    return net_income / assets if assets != 0 else None

def roce(ebit, capital_employed):
    return ebit / capital_employed if capital_employed != 0 else None

def roic(nopat, invested_capital):
    return nopat / invested_capital if invested_capital != 0 else None


# =====================================================
# PER SHARE RATIOS
# =====================================================

def eps(net_income, shares):
    return net_income / shares

def bvps(equity, shares):
    return equity / shares

def cashflow_per_share(cfo, shares):
    return cfo / shares

def fcf_per_share(fcf, shares):
    return fcf / shares


# =====================================================
# COVERAGE & SUSTAINABILITY
# =====================================================

def dividend_payout(dividends, net_income):
    return dividends / net_income if net_income != 0 else None

def dividend_coverage(net_income, dividends):
    return net_income / dividends if dividends != 0 else None

def dscr(cfo, debt_service):
    return cfo / debt_service if debt_service != 0 else None

def cash_interest_coverage(cfo, interest):
    return cfo / interest if interest != 0 else None


# =====================================================
# EFFICIENCY RATIOS
# =====================================================

def asset_turnover(revenue, assets):
    return revenue / assets

def inventory_turnover(cogs, inventory):
    return cogs / inventory if inventory != 0 else None

def receivables_turnover(revenue, receivables):
    return revenue / receivables if receivables != 0 else None

def payables_turnover(cogs, payables):
    return cogs / payables if payables != 0 else None

def cash_conversion_cycle(inv_days, rec_days, pay_days):
    return inv_days + rec_days - pay_days
