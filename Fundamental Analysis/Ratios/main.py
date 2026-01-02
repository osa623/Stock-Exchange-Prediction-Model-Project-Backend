from ratio import *  # This should contain all ratio functions
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
# WRITE OUTPUT
# =========================
def write_output(company, results):
    # Append consolidated analysis to the shared analysis file (don't overwrite)
    fname = "../ABC_Corp_income_analysis.txt"
    sep = "\n\n=== Analysis appended: " + datetime.utcnow().isoformat() + " UTC ===\n"
    with open(fname, "a", encoding="utf-8") as f:
        f.write(sep)
        f.write(f"Company: {company}\n")

        # results currently maps year -> {metric: value, ...}
        # invert it to metric -> {year: value}
        years = sorted(results.keys())
        # collect metric names from first year's dict (if any)
        sample = results[years[0]] if years else {}
        metric_names = list(sample.keys()) if isinstance(sample, dict) else []

        for metric in metric_names:
            f.write(f"\n{metric}\n")
            f.write("-" * len(metric) + "\n")
            for y in years:
                year_vals = results.get(y, {}) or {}
                val = year_vals.get(metric)
                if val is None:
                    f.write(f"{y}: N/A\n")
                elif isinstance(val, float):
                    f.write(f"{y}: {round(val, 4)}\n")
                else:
                    f.write(f"{y}: {val}\n")
    print("Appended:", fname)

# =========================
# MAIN
# =========================
if __name__ == "__main__":

    d = load_data("../ABC_Corp_income.txt")

    results = {}

# If ebitda isn't provided in the data, derive it from ebit + depreciation + amortization
    if "ebitda" not in d:
        d["ebitda"] = {
            y: (
                d.get("ebit", {}).get(y, 0)
                + d.get("depreciation", {}).get(y, 0)
                + d.get("amortization", {}).get(y, 0)
            )
            for y in d["years"]
        }

    # Calculate total debt first
    total_debt_dict = {y: d["short_term_debt"][y] + d["long_term_debt"][y] for y in d["years"]}

    for y in d["years"]:
        eps_v = eps(d["net_income"][y], d["shares_outstanding"][y])
        bvps_v = bvps(d["equity"][y], d["shares_outstanding"][y])
        price = d["market_price"]
        mcap = market_cap(price, d["shares_outstanding"][y])
        ev = enterprise_value(mcap, total_debt_dict[y], d["cash"][y])

        results[y] = {
            "Price": price,
            "Market Capitalization": mcap,
            "P/E Ratio": pe_ratio(price, eps_v),
            "P/B Ratio": pb_ratio(price, bvps_v),
            "P/S Ratio": ps_ratio(price, d["revenue"][y], d["shares_outstanding"][y]),
            "Earnings Yield": earnings_yield(eps_v, price),
            "Enterprise Value": ev,
            "EV / EBITDA": ev_ebitda(ev, d["ebitda"][y]),
            "EV / EBIT": ev_ebit(ev, d["ebit"][y]),
            "EV / Sales": ev_sales(ev, d["revenue"][y]),
        }

    write_output(d["company_name"], results)

