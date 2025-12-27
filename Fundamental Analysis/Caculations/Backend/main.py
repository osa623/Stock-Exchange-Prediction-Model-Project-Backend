# =====================================================
# MAIN
# =====================================================

import math
from income import *

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




    results = {
        "1. Revenue Growth Rate": rev_growth,
        "2. Gross Profit": gp,
        "3. Gross Profit Margin": gp_margin,
        "4. Operating Profit (EBIT)": op,
        "5. Operating Margin": op_margin,
        "6. EBITDA": eb,
        "7. EBITDA Margin": ebitda_m,
        "8. Net Profit Margin": net_m,
        "9. Effective Tax Rate": eff_tax,
        "10. Interest Coverage Ratio": interest_cov,
        "11. Earnings Quality (Accrual)": accrual,
        "12. Operating Expense Ratio": op_exp_ratio,
        "13. Cost Structure Breakdown": cost_struct,
        
        "1. Operating Leverage": op_leverage,
        "2. Contribution Margin": contrib_margin,
        "3. Break Even Revenue": break_even,
        "4. Earnings Growth": earn_growth,
        "5. EBIT vs Revenue Growth": ebit_vs_rev,
        "6. Expense Elasticity": exp_elastic,
        "7. Core Earnings": core,
        "8. Normalized Earnings": norm_earn,
        "9. Earnings Volatility": volatility,
        "10. Operating Margin Trend": op_margin_tr,
        "11. Pricing Power": pricing_power,
        "12. Cost Inflation Absorption": cost_absorb,
        "13. Earnings Quality Score": eq_score,

        "1. Incremental Margin": inc_margin,
        "2. Incremental EBITDA Margin": inc_ebitda_margin,
        "3. Recurring Earnings Ratio": recurring_ratio,
        "4. Profit Conversion Ratio": profit_conversion,
        "5. Depreciation Intensity": dep_intensity,
        "6. Earnings Sensitivity to Costs": earn_sensitivity,
        "7. Operating Safety Margin": op_safety,
        "8. Fixed Cost Coverage": fixed_cov,
        "9. Growth Persistence Index": growth_persistence,
        "10. Margin Stability Score": margin_stability,
        "11. Earnings Power": earn_power,
        "12. Pre-Tax Return Proxy": pretax_return,

        
    }

    write_output(d["company_name"], years, results)
