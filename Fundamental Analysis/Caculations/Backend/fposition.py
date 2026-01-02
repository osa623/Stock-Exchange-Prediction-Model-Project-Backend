

# =====================================================
# STATEMENT OF FINANCIAL POSITION CALCULATIONS
# =====================================================

def net_asset_value(total_assets, total_liabilities):
    return {y: total_assets[y] - total_liabilities[y] for y in total_assets}

def nav_per_share(nav, shares):
    return {y: nav[y] / shares[y] for y in nav}

def tangible_net_worth(equity, intangibles):
    return {y: equity[y] - intangibles[y] for y in equity}

def book_value_per_share(equity, shares):
    return {y: equity[y] / shares[y] for y in equity}

def working_capital(current_assets, current_liabilities):
    return {y: current_assets[y] - current_liabilities[y] for y in current_assets}

def current_ratio(current_assets, current_liabilities):
    return {y: current_assets[y] / current_liabilities[y] for y in current_assets}

def quick_ratio(ca, inventory, cl):
    return {y: (ca[y] - inventory[y]) / cl[y] for y in ca}

def cash_ratio(cash, cl):
    return {y: cash[y] / cl[y] for y in cash}

def total_debt(st_debt, lt_debt):
    return {y: st_debt[y] + lt_debt[y] for y in st_debt}

def debt_to_equity(debt, equity):
    return {y: debt[y] / equity[y] for y in debt}

def debt_to_assets(debt, assets):
    return {y: debt[y] / assets[y] for y in debt}

def equity_ratio(equity, assets):
    return {y: equity[y] / assets[y] for y in equity}

def long_term_debt_ratio(lt_debt, assets):
    return {y: lt_debt[y] / assets[y] for y in assets}

def capital_employed(equity, lt_debt):
    return {y: equity[y] + lt_debt[y] for y in equity}

def net_debt(debt, cash):
    return {y: debt[y] - cash[y] for y in debt}

def net_working_capital_ratio(wc, revenue):
    return {y: wc[y] / revenue[y] for y in wc}

def fixed_asset_ratio(fixed_assets, total_assets):
    return {y: fixed_assets[y] / total_assets[y] for y in fixed_assets}

def intangible_asset_ratio(intangibles, assets):
    return {y: intangibles[y] / assets[y] for y in assets}

def inventory_ratio(inventory, assets):
    return {y: inventory[y] / assets[y] for y in assets}

def receivables_ratio(receivables, assets):
    return {y: receivables[y] / assets[y] for y in assets}

def roa(net_income, assets):
    return {y: net_income[y] / assets[y] for y in net_income}

def roe(net_income, equity):
    return {y: net_income[y] / equity[y] for y in net_income}

def roce(ebit, capital_employed):
    return {y: ebit[y] / capital_employed[y] for y in ebit}

def asset_turnover(revenue, assets):
    return {y: revenue[y] / assets[y] for y in revenue}

def financial_leverage(assets, equity):
    return {y: assets[y] / equity[y] for y in assets}

def net_asset_growth(nav, years):
    return {years[i]: (nav[years[i]] - nav[years[i-1]]) / nav[years[i-1]]
            for i in range(1, len(years))}

def defensive_interval_ratio(cash, receivables, daily_expenses):
    return {y: (cash[y] + receivables[y]) / daily_expenses[y] for y in cash}

def net_liquid_assets(ca, inventory, total_liabilities):
    return {y: ca[y] - inventory[y] - total_liabilities[y] for y in ca}

def liquidity_coverage_ratio(ca, cl):
    return {y: ca[y] / cl[y] for y in ca}

def ncav(ca, total_liabilities):
    return {y: ca[y] - total_liabilities[y] for y in ca}

def ncav_per_share(ncav, shares):
    return {y: ncav[y] / shares[y] for y in ncav}

def balance_sheet_margin_of_safety(ncav, market_cap):
    return {y: ncav[y] / market_cap[y] for y in ncav}

def asset_quality_ratio(tangible_assets, total_assets):
    return {y: tangible_assets[y] / total_assets[y] for y in total_assets}

def capital_intensity_ratio(assets, revenue):
    return {y: assets[y] / revenue[y] for y in assets}

def debt_maturity_ratio(st_debt, total_debt):
    return {y: st_debt[y] / total_debt[y] for y in st_debt}

def structural_leverage_ratio(debt, capital_employed):
    return {y: debt[y] / capital_employed[y] for y in debt}

def equity_buffer_ratio(equity, assets):
    return {y: equity[y] / assets[y] for y in equity}

def retained_earnings_ratio(retained, equity):
    return {y: retained[y] / equity[y] for y in equity}

def shareholder_dilution_risk(shares, years):
    return {years[i]: (shares[years[i]] - shares[years[i-1]]) / shares[years[i-1]]
            for i in range(1, len(years))}

def net_operating_assets(op_assets, op_liabilities):
    return {y: op_assets[y] - op_liabilities[y] for y in op_assets}

def financial_obligations(debt, cl):
    return {y: debt[y] + cl[y] for y in debt}

def capital_preservation_ratio(equity, intangibles):
    return {y: (equity[y] - intangibles[y]) / equity[y] for y in equity}
