# =====================================================
# MAIN
# =====================================================

import math
from income import *
from fposition import *
from cashflow import *

# =====================================================
# OUTPUT
# =====================================================
def write_output(company, years, results):
    fname = company.replace(" ", "_") + "_income_analysis.txt"
    with open(fname, "w", encoding="utf-8") as f:
        for name, values in results.items():
            f.write(f"\n{name}\n")
            f.write("-" * len(name) + "\n")
            # Nested dicts (e.g., cost structure)
            if isinstance(values, dict) and all(isinstance(v, dict) for v in values.values()):
                for sub, subvals in values.items():
                    f.write(f"\n{sub}\n")
                    for y in years:
                        val = subvals.get(y)
                        if val is None:
                            f.write(f"{y}: N/A\n")
                        elif isinstance(val, (int, float)):
                            f.write(f"{y}: {round(val, 4)}\n")
                        else:
                            f.write(f"{y}: {val}\n")

            # Dicts keyed by year (e.g., margins, growth rates)
            elif isinstance(values, dict):
                for y in years:
                    val = values.get(y)
                    if val is None:
                        f.write(f"{y}: N/A\n")
                    elif isinstance(val, (int, float)):
                        f.write(f"{y}: {round(val, 4)}\n")
                    else:
                        f.write(f"{y}: {val}\n")

            # Scalar values (e.g., volatility, pricing_power, scores)
            elif isinstance(values, (int, float)):
                f.write(f"{round(values, 4)}\n")

            # Fallback for other types
            else:
                f.write(f"{values}\n")

    print("Saved:", fname)




# =========================
# MAIN RUN FUNCTION
# =========================




if __name__ == "__main__":
    d = load_data("ABC_Corp_income.txt")
    years = d["years"]

    # Basic statements
    gp = gross_profit(d["revenue"], d["cogs"])
    gp_margin = gross_margin(gp, d["revenue"])
    op = operating_profit(gp, d["rd"], d["sga"])
    op_margin = operating_margin(op, d["revenue"])
    eb = ebitda(op, d["depreciation"], d["amortization"])

    # Core metrics
    rev_growth = revenue_growth(d["revenue"], years)
    ebitda_m = ebitda_margin(eb, d["revenue"])
    net_m = net_margin(d["net_income"], d["revenue"])
    eff_tax = effective_tax_rate(d["income_tax"], op)
    interest_cov = interest_coverage(op, d["interest_expense"])
    accrual = earnings_quality_accrual(d["net_income"], d["cash_from_operations"])
    op_exp_ratio = operating_expense_ratio(d["rd"], d["sga"], d["revenue"])
    cost_struct = cost_structure(d["cogs"], d["rd"], d["sga"], d["revenue"])

    # Advanced metrics
    op_leverage = operating_leverage(op, d["revenue"], years)
    contrib_margin = contribution_margin(d["revenue"], d["cogs"])
    break_even = break_even_revenue(d["rd"], d["sga"], contrib_margin)
    earn_growth = earnings_growth(d["net_income"], years)
    ebit_vs_rev = ebit_vs_revenue_growth(op, d["revenue"], years)
    exp_elastic = expense_elasticity(d["rd"], d["sga"], d["revenue"], years)
    core = core_earnings(op, eff_tax)
    norm_earn = normalized_earnings(d["net_income"])
    volatility = earnings_volatility(earn_growth)
    op_margin_tr = operating_margin_trend(op_margin, years)
    pricing_power = pricing_power_indicator(gp_margin)
    cost_absorb = cost_inflation_absorption(gp_margin, years)
    eq_score = earnings_quality_score(accrual, volatility, op_margin_tr)
    inc_margin = incremental_margin(op, d["revenue"], years)
    inc_ebitda_margin = incremental_ebitda_margin(eb, d["revenue"], years)

    recurring_ratio = recurring_earnings_ratio(d["net_income"], d["one_off_items"])
    profit_conversion = profit_conversion_ratio(d["net_income"], d["cash_from_operations"])
    dep_intensity = depreciation_intensity(d["depreciation"], d["revenue"])

    earn_sensitivity = earnings_sensitivity_to_costs(d["cogs"], d["revenue"], years)
    op_safety = operating_safety_margin(op, d["revenue"])
    fixed_cov = fixed_cost_coverage(eb, d["fixed_costs"])

    growth_persistence = growth_persistence_index(rev_growth)
    margin_stability = margin_stability_score(op_margin)

    earn_power = earnings_power(op, eff_tax)
    pretax_return = pre_tax_return_proxy(op, d["revenue"])


    nav = net_asset_value(d["total_assets"], d["total_liabilities"])
    nav_ps = nav_per_share(nav, d["shares_outstanding"])

    tnw = tangible_net_worth(d["equity"], d["intangibles"])
    bvps = book_value_per_share(d["equity"], d["shares_outstanding"])

    wc = working_capital(d["current_assets"], d["current_liabilities"])
    current_r = current_ratio(d["current_assets"], d["current_liabilities"])
    quick_r = quick_ratio(d["current_assets"], d["inventory"], d["current_liabilities"])
    cash_r = cash_ratio(d["cash"], d["current_liabilities"])

    debt = total_debt(d["short_term_debt"], d["long_term_debt"])
    debt_equity = debt_to_equity(debt, d["equity"])
    debt_assets = debt_to_assets(debt, d["total_assets"])
    equity_r = equity_ratio(d["equity"], d["total_assets"])
    lt_debt_r = long_term_debt_ratio(d["long_term_debt"], d["total_assets"])

    cap_emp = capital_employed(d["equity"], d["long_term_debt"])
    net_debt_v = net_debt(debt, d["cash"])


    nwc_ratio = net_working_capital_ratio(wc, d["revenue"])

    fixed_asset_r = fixed_asset_ratio(d["fixed_assets"], d["total_assets"])
    intangible_r = intangible_asset_ratio(d["intangibles"], d["total_assets"])
    inventory_r = inventory_ratio(d["inventory"], d["total_assets"])
    receivables_r = receivables_ratio(d["receivables"], d["total_assets"])

    roa_v = roa(d["net_income"], d["total_assets"])
    roe_v = roe(d["net_income"], d["equity"])
    roce_v = roce(op, cap_emp)

    asset_turn = asset_turnover(d["revenue"], d["total_assets"])
    fin_leverage = financial_leverage(d["total_assets"], d["equity"])

    nav_growth = net_asset_growth(nav, years)

    defensive_interval = defensive_interval_ratio(
        d["cash"],
        d["receivables"],
        d["daily_operating_expenses"]
    )

    net_liquid = net_liquid_assets(
        d["current_assets"],
        d["inventory"],
        d["total_liabilities"]
    )

    liquidity_cov = liquidity_coverage_ratio(
        d["current_assets"],
        d["current_liabilities"]
    )

    ncav_v = ncav(d["current_assets"], d["total_liabilities"])



    ncav_ps = ncav_per_share(ncav_v, d["shares_outstanding"])
    bs_margin_safety = balance_sheet_margin_of_safety(ncav_v, d["market_cap"])

    tangible_assets = {
        y: d["total_assets"][y] - d["intangibles"][y]
        for y in years
    }

    asset_quality = asset_quality_ratio(tangible_assets, d["total_assets"])
    capital_intensity = capital_intensity_ratio(d["total_assets"], d["revenue"])

    debt_maturity = debt_maturity_ratio(
        d["short_term_debt"],
        debt
    )

    struct_leverage = structural_leverage_ratio(debt, cap_emp)
    equity_buffer = equity_buffer_ratio(d["equity"], d["total_assets"])
    retained_ratio = retained_earnings_ratio(d["retained_earnings"], d["equity"])

    dilution_risk = shareholder_dilution_risk(d["shares_outstanding"], years)

    net_oper_assets = net_operating_assets(
        d["operating_assets"],
        d["operating_liabilities"]
    )

    fin_obligations = financial_obligations(debt, d["current_liabilities"])

    capital_preservation = capital_preservation_ratio(
        d["equity"],
        d["intangibles"]
    )



    fcf = free_cash_flow(d["cash_from_operations"], d["capex"])
    fcf_ps = free_cash_flow_per_share(fcf, d["shares_outstanding"])
    ccr = cash_conversion_ratio(d["cash_from_operations"], d["net_income"])
    ocf_margin = operating_cash_flow_margin(d["cash_from_operations"], d["revenue"])
    capex_r = capex_ratio(d["capex"], d["cash_from_operations"])
    ocf_debt = ocf_to_debt_ratio(d["cash_from_operations"], debt)

    net_inv_cf = net_investing_cash_flow(d["capex"], d["asset_sales"])
    asset_reinv = asset_reinvestment_ratio(d["capex"], d["depreciation"])
    net_debt_move = net_debt_issued(d["debt_issued"], d["debt_repaid"])
    div_payout = dividend_payout_cash(d["dividends_paid"], d["cash_from_operations"])

    debt_cov_fcf = debt_coverage_ratio_fcf(fcf, debt)
    cf_to_ni = cash_flow_to_net_income(d["cash_from_operations"], d["net_income"])
    croa = cash_return_on_assets(d["cash_from_operations"], d["total_assets"])
    croe = cash_return_on_equity(d["cash_from_operations"], d["equity"])
    cf_adequacy = cash_flow_adequacy_ratio(
        d["cash_from_operations"],
        d["capex"],
        d["debt_repaid"],
        d["dividends_paid"]
    )

    fcf_yield = free_cash_flow_yield(fcf, d["market_cap"])

    net_cf = net_cash_flow(
        d["cash_from_operations"],
        d["cash_from_investing"],
        d["cash_from_financing"]
    )

    cf_vol = cash_flow_volatility(d["cash_from_operations"], years)
    cash_op_lev = operating_leverage_cash(
        d["cash_from_operations"],
        d["revenue"],
        years
    )



    results = {
        "IS1. Revenue Growth Rate": rev_growth,
        "IS2. Gross Profit": gp,
        "IS3. Gross Profit Margin": gp_margin,
        "IS4. Operating Profit (EBIT)": op,
        "IS5. Operating Margin": op_margin,
        "IS6. EBITDA": eb,
        "IS7. EBITDA Margin": ebitda_m,
        "IS8. Net Profit Margin": net_m,
        "IS9. Effective Tax Rate": eff_tax,
        "IS10. Interest Coverage Ratio": interest_cov,
        "IS11. Earnings Quality (Accrual)": accrual,
        "IS12. Operating Expense Ratio": op_exp_ratio,
        "IS13. Cost Structure Breakdown": cost_struct,
        
        "IS1. Operating Leverage": op_leverage,
        "IS2. Contribution Margin": contrib_margin,
        "IS3. Break Even Revenue": break_even,
        "IS4. Earnings Growth": earn_growth,
        "IS5. EBIT vs Revenue Growth": ebit_vs_rev,
        "IS6. Expense Elasticity": exp_elastic,
        "IS7. Core Earnings": core,
        "IS8. Normalized Earnings": norm_earn,
        "IS9. Earnings Volatility": volatility,
        "IS10. Operating Margin Trend": op_margin_tr,
        "IS11. Pricing Power": pricing_power,
        "IS12. Cost Inflation Absorption": cost_absorb,
        "IS13. Earnings Quality Score": eq_score,

        "IS1. Incremental Margin": inc_margin,
        "IS2. Incremental EBITDA Margin": inc_ebitda_margin,
        "IS3. Recurring Earnings Ratio": recurring_ratio,
        "IS4. Profit Conversion Ratio": profit_conversion,
        "IS5. Depreciation Intensity": dep_intensity,
        "IS6. Earnings Sensitivity to Costs": earn_sensitivity,
        "IS7. Operating Safety Margin": op_safety,
        "IS8. Fixed Cost Coverage": fixed_cov,
        "IS9. Growth Persistence Index": growth_persistence,
        "IS10. Margin Stability Score": margin_stability,
        "IS11. Earnings Power": earn_power,
        "IS12. Pre-Tax Return Proxy": pretax_return,

        "SFP 1. Net Asset Value": nav,
        "SFP 2. NAV per Share": nav_ps,
        "SFP 3. Tangible Net Worth": tnw,
        "SFP 4. Book Value per Share": bvps,
        "SFP 5. Working Capital": wc,
        "SFP 6. Current Ratio": current_r,
        "SFP 7. Quick Ratio": quick_r,
        "SFP 8. Cash Ratio": cash_r,
        "SFP 9. Total Debt": debt,
        "SFP 10. Debt to Equity": debt_equity,
        "SFP 11. Debt to Assets": debt_assets,
        "SFP 12. Equity Ratio": equity_r,
        "SFP 13. Long-Term Debt Ratio": lt_debt_r,
        "SFP 14. Capital Employed": cap_emp,
        "SFP 15. Net Debt": net_debt_v,

        "SFP 16. Net Working Capital Ratio": nwc_ratio,
        "SFP 17. Fixed Asset Ratio": fixed_asset_r,
        "SFP 18. Intangible Asset Ratio": intangible_r,
        "SFP 19. Inventory Ratio": inventory_r,
        "SFP 20. Receivables Ratio": receivables_r,
        "SFP 21. Return on Assets (ROA)": roa_v,
        "SFP 22. Return on Equity (ROE)": roe_v,
        "SFP 23. Return on Capital Employed (ROCE)": roce_v,
        "SFP 24. Asset Turnover": asset_turn,
        "SFP 25. Financial Leverage": fin_leverage,
        "SFP 26. Net Asset Growth Rate": nav_growth,
        "SFP 27. Defensive Interval Ratio": defensive_interval,
        "SFP 28. Net Liquid Assets": net_liquid,
        "SFP 29. Liquidity Coverage Ratio": liquidity_cov,
        
        "SFP 30. Net Current Asset Value (NCAV)": ncav_v,
        "SFP 31. NCAV per Share": ncav_ps,
        "SFP 32. Balance Sheet Margin of Safety": bs_margin_safety,
        "SFP 33. Asset Quality Ratio": asset_quality,
        "SFP 34. Capital Intensity Ratio": capital_intensity,
        "SFP 35. Debt Maturity Ratio": debt_maturity,
        "SFP 36. Structural Leverage Ratio": struct_leverage,
        "SFP 37. Equity Buffer Ratio": equity_buffer,
        "SFP 38. Retained Earnings Ratio": retained_ratio,
        "SFP 39. Shareholder Dilution Risk": dilution_risk,
        "SFP 40. Net Operating Assets (NOA)": net_oper_assets,
        "SFP 41. Financial Obligations": fin_obligations,
        "SFP 42. Capital Preservation Ratio": capital_preservation,


        "SCF 1. Free Cash Flow": fcf,
        "SCF 2. Free Cash Flow per Share": fcf_ps,
        "SCF 3. Cash Conversion Ratio": ccr,
        "SCF 4. OCF Margin": ocf_margin,
        "SCF 5. CapEx Ratio": capex_r,
        "SCF 6. OCF to Debt Ratio": ocf_debt,
        "SCF 7. Net Investing Cash Flow": net_inv_cf,
        "SCF 8. Asset Reinvestment Ratio": asset_reinv,
        "SCF 9. Net Debt Issued / Repaid": net_debt_move,
        "SCF 10. Dividend Payout (Cash)": div_payout,
        "SCF 11. Debt Coverage Ratio (FCF)": debt_cov_fcf,
        "SCF 12. Cash Flow to Net Income": cf_to_ni,
        "SCF 13. Cash ROA": croa,
        "SCF 14. Cash ROE": croe,
        "SCF 15. Cash Flow Adequacy Ratio": cf_adequacy,
        "SCF 16. Free Cash Flow Yield": fcf_yield,
        "SCF 17. Net Cash Flow": net_cf,
        "SCF 18. Cash Flow Volatility": cf_vol,
        "SCF 19. Operating Leverage (Cash)": cash_op_lev,




        
    }

    write_output(d["company_name"], years, results)
