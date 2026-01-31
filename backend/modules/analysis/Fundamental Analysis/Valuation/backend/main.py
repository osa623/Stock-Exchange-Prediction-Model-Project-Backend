from value import *
from datetime import datetime

# =========================
# LOAD DATA
# =========================
def load_data(path):
    data = {}
    with open(path, "r", encoding="utf-8") as f:
        exec(f.read(), {}, data)
    return data

# =========================
# WRITE OUTPUT (APPEND)
# =========================
def write_output(company, results):
    fname = "../ABC_Corp_income_analysis.txt"
    sep = "\n\n=== Valuation Analysis appended: " + datetime.utcnow().isoformat() + " UTC ===\n"

    with open(fname, "a", encoding="utf-8") as f:
        f.write(sep)
        f.write(f"Company: {company}\n")

        years = sorted(results.keys())
        metrics = results[years[0]].keys()

        for metric in metrics:
            f.write(f"\n{metric}\n")
            f.write("-" * len(metric) + "\n")
            for y in years:
                val = results[y][metric]
                f.write(f"{y}: {round(val, 4) if isinstance(val, float) else val}\n")

    print("Valuation appended:", fname)

# =========================
# MAIN
# =========================
if __name__ == "__main__":

    d = load_data("../ABC_Corp_income.txt")
    results = {}

    for y in d["years"]:
        # --- working capital and delta ---
        wc = {yr: d.get("current_assets", {}).get(yr, 0) - d.get("current_liabilities", {}).get(yr, 0) for yr in d["years"]}
        delta_wc = delta_working_capital(wc, d["years"])

        # --- FCFF (scalar and dict) ---
        fcff_scalar = calc_fcff(
            d["ebit"][y],
            d["tax_rate"],
            d["depreciation"][y],
            d["capex"][y],
            delta_wc.get(y, 0)
        )

        tax_dict = {yr: d.get("tax_rate", 0) for yr in d["years"]}
        fcff_dict = fcff(d.get("ebit", {}), tax_dict, d.get("depreciation", {}), d.get("capex", {}), delta_wc)

        firm_val = dcf_firm_value(
            fcff_scalar,
            d["wacc"],
            d["terminal_growth"]
        )

        # firm value from the FCFF dict (multi-year DCF)
        firm_val_from_dict = firm_value(fcff_dict, d["wacc"], d["terminal_growth"]) if fcff_dict else None
        total_debt_y = d.get("total_debt", {}).get(y,
                     d.get("short_term_debt", {}).get(y, 0) + d.get("long_term_debt", {}).get(y, 0))
        equity_val = firm_val - (total_debt_y - d.get("cash", {}).get(y, 0))

        intrinsic_price = equity_val / d["shares_outstanding"][y]

        fcfe_scalar = calc_fcfe(
            d["net_income"][y],
            d["depreciation"][y],
            d["capex"][y],
            d.get("delta_wc", {}).get(y, 0),
            d.get("net_borrowing", {}).get(y, 0)
        )

        # FCFE dict and per-share (dict-based)
        raw_net_borrowing = d.get("net_borrowing", {})
        net_borrowing_dict = {yr: raw_net_borrowing.get(yr, 0) for yr in d["years"]}
        fcfe_dict = fcfe(d.get("net_income", {}), d.get("depreciation", {}), d.get("capex", {}), delta_wc, net_borrowing_dict)
        fcfe_per_share_dict = None
        if fcfe_dict:
            total_fcfe_value = fcfe_dcf(fcfe_dict, d.get("cost_of_equity", 0), d.get("terminal_growth", 0))
            fcfe_per_share_dict = total_fcfe_value / d.get("shares_outstanding", {}).get(y, 1)

        fcfe_value = fcfe_dcf(
            fcfe_scalar,
            d["cost_of_equity"],
            d["terminal_growth"]
        ) / d["shares_outstanding"][y]

        cash_y = d.get("cash", {}).get(y, 0)
        net_debt_y = total_debt_y - cash_y

        # Additional metrics using functions in value.py
        working_capital_y = wc.get(y, 0)
        delta_wc_y = delta_wc.get(y, 0)
        fcff_dict_y = fcff_dict.get(y) if isinstance(fcff_dict, dict) else None
        fcfe_dict_y = fcfe_dict.get(y) if isinstance(fcfe_dict, dict) else None

        firm_eq_from_dict = None
        if firm_val_from_dict is not None:
            firm_eq_from_dict = equity_value_from_firm(firm_val_from_dict, net_debt_y)

        # per-share DDM using dividends if available
        dividend = d.get("dividends_paid", {}).get(y, 0)
        dividend_per_share = dividend / d.get("shares_outstanding", {}).get(y, 1) if dividend else 0
        ddm = ddm_gordon(dividend_per_share, d.get("cost_of_equity", 0.0), d.get("terminal_growth", 0.0)) if dividend_per_share > 0 else None

        residual_inc = residual_income(d.get("net_income", {}).get(y, 0), d.get("equity", {}).get(y, 0), d.get("cost_of_equity", 0))
        adj_nav = adjusted_nav(d.get("total_assets", {}).get(y, 0), d.get("total_liabilities", {}).get(y, 0))
        liq_value = liquidation_value(d.get("cash", {}).get(y, 0), d.get("total_liabilities", {}).get(y, 0))
        mos = margin_of_safety(intrinsic_price, d.get("market_price", 0)) if d.get("market_price", 0) else None
        safe_price = safe_buy_price(intrinsic_price, 0.2) if intrinsic_price else None
        expected_ret = expected_annual_return(intrinsic_price, d.get("market_price", 0), 1) if d.get("market_price", 0) else None

        epv = earnings_power_value(
            d["normalized_ebit"],
            d["tax_rate"],
            d["wacc"],
            net_debt_y,
            d["shares_outstanding"][y]
        )

        results[y] = {
            "FCFF": fcff_scalar,
            "FCFF (dict)": fcff_dict_y,
            "Firm Value (DCF)": firm_val,
            "Firm Value (from FCFF dict)": firm_val_from_dict,
            "Equity Value": equity_val,
            "Equity Value (from FCFF dict)": firm_eq_from_dict,
            "Intrinsic Price (DCF)": intrinsic_price,
            "FCFE per Share": fcfe_value,
            "FCFE per Share (from FCFE dict)": fcfe_per_share_dict,
            "FCFE (dict)": fcfe_dict_y,
            "Working Capital": working_capital_y,
            "Delta Working Capital": delta_wc_y,
            "DDM (Gordon)": ddm,
            "Residual Income": residual_inc,
            "Adjusted NAV": adj_nav,
            "Liquidation Value": liq_value,
            "Margin of Safety": mos,
            "Safe Buy Price (20% MOS)": safe_price,
            "Expected Annual Return (1y)": expected_ret,
            "EPV per Share": epv
        }

    write_output(d["company_name"], results)
