# =====================================================
# STATEMENT OF CASH FLOWS (SCF)
# =====================================================

import statistics



def operating_cash_flow(cfo):
    return cfo


def free_cash_flow(cfo, capex):
    return {y: cfo[y] - capex[y] for y in cfo}


def free_cash_flow_per_share(fcf, shares):
    return {y: fcf[y] / shares[y] for y in fcf}


def cash_conversion_ratio(cfo, net_income):
    return {
        y: cfo[y] / net_income[y] if net_income[y] != 0 else None
        for y in cfo
    }


def operating_cash_flow_margin(cfo, revenue):
    return {y: cfo[y] / revenue[y] for y in cfo}


def capex_ratio(capex, cfo):
    return {y: capex[y] / cfo[y] if cfo[y] != 0 else None for y in capex}


def ocf_to_debt_ratio(cfo, total_debt):
    return {
        y: cfo[y] / total_debt[y] if total_debt[y] != 0 else None
        for y in cfo
    }



def net_investing_cash_flow(capex, asset_sales):
    return {y: asset_sales[y] - capex[y] for y in capex}


def asset_reinvestment_ratio(capex, depreciation):
    return {
        y: capex[y] / depreciation[y] if depreciation[y] != 0 else None
        for y in capex
    }


def net_debt_issued(debt_issued, debt_repaid):
    return {y: debt_issued[y] - debt_repaid[y] for y in debt_issued}


def dividend_payout_cash(dividends, cfo):
    return {
        y: dividends[y] / cfo[y] if cfo[y] != 0 else None
        for y in dividends
    }



def debt_coverage_ratio_fcf(fcf, total_debt):
    return {
        y: fcf[y] / total_debt[y] if total_debt[y] != 0 else None
        for y in fcf
    }


def cash_flow_to_net_income(cfo, net_income):
    return {
        y: cfo[y] / net_income[y] if net_income[y] != 0 else None
        for y in cfo
    }


def cash_return_on_assets(cfo, total_assets):
    return {y: cfo[y] / total_assets[y] for y in cfo}


def cash_return_on_equity(cfo, equity):
    return {y: cfo[y] / equity[y] for y in cfo}


def cash_flow_adequacy_ratio(cfo, capex, debt_repaid, dividends):
    return {
        y: cfo[y] / (capex[y] + debt_repaid[y] + dividends[y])
        if (capex[y] + debt_repaid[y] + dividends[y]) != 0 else None
        for y in cfo
    }


def free_cash_flow_yield(fcf, market_cap):
    return {y: fcf[y] / market_cap[y] for y in fcf}



def net_cash_flow(cfo, cfi, cff):
    return {y: cfo[y] + cfi[y] + cff[y] for y in cfo}


def cash_flow_volatility(cfo, years):
    values = [cfo[y] for y in years]
    return statistics.stdev(values) if len(values) > 1 else 0


def operating_leverage_cash(cfo, revenue, years):
    lev = {}
    for i in range(1, len(years)):
        y0, y1 = years[i - 1], years[i]
        cfo_g = (cfo[y1] - cfo[y0]) / abs(cfo[y0])
        rev_g = (revenue[y1] - revenue[y0]) / revenue[y0]
        lev[y1] = cfo_g / rev_g if rev_g != 0 else None
    return lev
