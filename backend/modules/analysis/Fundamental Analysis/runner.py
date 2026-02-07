def get_basic_stock_data(symbol: str) -> dict:
    # Stub: replace with real market data source later
    return {
        "symbol": symbol.upper(),
        "company_name": f"{symbol.upper()} Corp",
        "price": 123.45,
    }

def get_full_fundamental_data(symbol: str) -> dict:
    basic = get_basic_stock_data(symbol)
    # Stubbed “premium” data
    return {
        **basic,
        "valuation_summary": {"intrinsic_value": 140.0, "margin_of_safety": 0.12},
        "ratios": {"pe": 18.2, "pb": 3.4, "roe": 0.19},
        "cashflow_summary": {"free_cash_flow": 5_200_000, "operating_cf": 7_900_000},
    }
