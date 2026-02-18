"""
Seed script — populates the MongoDB 'reports' collection with sample data
mirroring the analysis module folder structure.

Usage:
    cd backend
    python -m modules.reports.seed
"""

import asyncio
from datetime import datetime, timezone
from db.mongo import get_mongo_db, close_mongo

SEED_REPORTS = [
    # ── Fundamental Analysis / Ratios ──────────────────────────────────
    {
        "category": "Fundamental Analysis",
        "subcategory": "Ratios",
        "title": "ABC Corp Ratio Analysis 2024",
        "symbol": "ABC",
        "access_level": "public",
        "summary": "Key valuation ratios for ABC Corp covering PE, PB, PS, EV/EBITDA, ROE, and ROA for fiscal year 2024.",
        "tags": ["ratios", "valuation", "ABC"],
        "data": {
            "pe_ratio": 15.2,
            "pb_ratio": 2.1,
            "ps_ratio": 1.8,
            "ev_ebitda": 10.5,
            "roe": 0.18,
            "roa": 0.09,
            "eps": 3.45,
            "dividend_yield": 0.025,
        },
        "raw_data": {
            "yearly": {
                "2022": {"pe": 14.1, "pb": 1.9, "roe": 0.16},
                "2023": {"pe": 14.8, "pb": 2.0, "roe": 0.17},
                "2024": {"pe": 15.2, "pb": 2.1, "roe": 0.18},
            }
        },
        "methodology": "Ratios computed from audited annual statements using standard formulas.",
    },
    {
        "category": "Fundamental Analysis",
        "subcategory": "Ratios",
        "title": "XYZ Inc Ratio Analysis 2024",
        "symbol": "XYZ",
        "access_level": "registered",
        "summary": "Comprehensive ratio set for XYZ Inc — profitability, liquidity, and leverage.",
        "tags": ["ratios", "XYZ", "profitability"],
        "data": {
            "pe_ratio": 22.6,
            "pb_ratio": 4.3,
            "current_ratio": 1.8,
            "debt_to_equity": 0.45,
            "roe": 0.24,
            "roa": 0.12,
        },
    },
    # ── Fundamental Analysis / Valuation ───────────────────────────────
    {
        "category": "Fundamental Analysis",
        "subcategory": "Valuation",
        "title": "ABC Corp DCF Valuation",
        "symbol": "ABC",
        "access_level": "premium",
        "summary": "Discounted Cash Flow valuation with 10-year projection and terminal value.",
        "tags": ["dcf", "valuation", "ABC"],
        "data": {
            "intrinsic_price": 52.30,
            "current_price": 48.00,
            "margin_of_safety": 0.082,
            "safe_buy_price": 44.60,
            "wacc": 0.095,
            "terminal_growth": 0.025,
        },
        "raw_data": {
            "projected_fcf": [5.2, 5.8, 6.3, 6.9, 7.4, 7.9, 8.3, 8.7, 9.1, 9.5],
            "terminal_value": 142.5,
            "discount_factors": [0.913, 0.834, 0.762, 0.696, 0.635, 0.580, 0.530, 0.484, 0.442, 0.404],
        },
        "methodology": "Two-stage DCF with WACC discount rate, Gordon Growth terminal value.",
        "metadata": {"model_version": "2.1", "analyst": "system", "confidence": "medium"},
    },
    {
        "category": "Fundamental Analysis",
        "subcategory": "Valuation",
        "title": "XYZ Inc Gordon Growth Model",
        "symbol": "XYZ",
        "access_level": "registered",
        "summary": "Dividend discount model using Gordon Growth for stable-dividend payers.",
        "tags": ["ddm", "gordon", "XYZ", "dividends"],
        "data": {
            "intrinsic_price": 38.50,
            "current_price": 35.00,
            "dividend_per_share": 1.20,
            "required_return": 0.10,
            "growth_rate": 0.04,
        },
    },
    # ── Fundamental Analysis / Calculations ────────────────────────────
    {
        "category": "Fundamental Analysis",
        "subcategory": "Calculations",
        "title": "ABC Corp Income Statement Analysis",
        "symbol": "ABC",
        "access_level": "public",
        "summary": "Revenue growth, gross/operating/net margins, EBITDA, and earnings quality metrics.",
        "tags": ["income", "margins", "ABC"],
        "data": {
            "revenue_growth": 0.12,
            "gross_margin": 0.42,
            "operating_margin": 0.18,
            "net_margin": 0.11,
            "ebitda": 25000000,
            "earnings_quality_score": 0.85,
        },
    },
    {
        "category": "Fundamental Analysis",
        "subcategory": "Calculations",
        "title": "ABC Corp Cash Flow Analysis",
        "symbol": "ABC",
        "access_level": "registered",
        "summary": "Free cash flow, cash conversion ratio, and cash flow adequacy assessment.",
        "tags": ["cashflow", "fcf", "ABC"],
        "data": {
            "free_cash_flow": 15000000,
            "fcf_per_share": 3.00,
            "cash_conversion_ratio": 0.92,
            "ocf_margin": 0.22,
            "capex_ratio": 0.08,
        },
    },
    {
        "category": "Fundamental Analysis",
        "subcategory": "Calculations",
        "title": "ABC Corp Balance Sheet Health",
        "symbol": "ABC",
        "access_level": "premium",
        "summary": "Working capital, current/quick ratios, debt structure, and capital preservation.",
        "tags": ["balance-sheet", "liquidity", "ABC"],
        "data": {
            "current_ratio": 2.1,
            "quick_ratio": 1.5,
            "cash_ratio": 0.8,
            "debt_to_equity": 0.35,
            "net_debt": 12000000,
            "working_capital": 30000000,
        },
        "raw_data": {
            "yearly": {
                "2022": {"current_ratio": 1.9, "debt_eq": 0.40},
                "2023": {"current_ratio": 2.0, "debt_eq": 0.38},
                "2024": {"current_ratio": 2.1, "debt_eq": 0.35},
            }
        },
    },
    # ── Fundamental Analysis / Forecasting ─────────────────────────────
    {
        "category": "Fundamental Analysis",
        "subcategory": "Forecasting",
        "title": "ABC Corp Revenue Forecast 2025-2027",
        "symbol": "ABC",
        "access_level": "premium",
        "summary": "Three-year revenue forecast using regression + seasonal adjustment.",
        "tags": ["forecast", "revenue", "ABC"],
        "data": {
            "forecast_2025": 280000000,
            "forecast_2026": 310000000,
            "forecast_2027": 340000000,
            "cagr": 0.10,
            "confidence_interval": "80%",
        },
        "methodology": "Linear regression on 5Y trailing revenue with seasonal decomposition.",
    },
    # ── Technical Analysis ─────────────────────────────────────────────
    {
        "category": "Technical Analysis",
        "subcategory": None,
        "title": "ABC Corp Moving Average Crossover",
        "symbol": "ABC",
        "access_level": "public",
        "summary": "50/200 day moving average crossover signal analysis.",
        "tags": ["technical", "moving-average", "ABC"],
        "data": {
            "ma_50": 47.50,
            "ma_200": 45.80,
            "signal": "bullish_crossover",
            "signal_date": "2025-12-15",
        },
    },
    {
        "category": "Technical Analysis",
        "subcategory": None,
        "title": "XYZ Inc RSI & MACD Analysis",
        "symbol": "XYZ",
        "access_level": "registered",
        "summary": "Relative Strength Index and MACD divergence assessment.",
        "tags": ["technical", "rsi", "macd", "XYZ"],
        "data": {
            "rsi_14": 62.3,
            "macd_signal": "neutral",
            "macd_histogram": 0.15,
        },
    },
    # ── Sentimental Analysis ───────────────────────────────────────────
    {
        "category": "Sentimental Analysis",
        "subcategory": None,
        "title": "ABC Corp News Sentiment Q4 2025",
        "symbol": "ABC",
        "access_level": "public",
        "summary": "Aggregated news sentiment score from 150+ articles.",
        "tags": ["sentiment", "news", "ABC"],
        "data": {
            "sentiment_score": 0.72,
            "articles_analyzed": 153,
            "positive_pct": 0.65,
            "negative_pct": 0.12,
            "neutral_pct": 0.23,
        },
    },
    # ── Economic Analysis ──────────────────────────────────────────────
    {
        "category": "Economic Analysis",
        "subcategory": None,
        "title": "Macro Economic Indicators Q4 2025",
        "symbol": None,
        "access_level": "public",
        "summary": "GDP growth, inflation, unemployment, and interest rate trends.",
        "tags": ["macro", "gdp", "inflation"],
        "data": {
            "gdp_growth": 0.023,
            "cpi_inflation": 0.031,
            "unemployment_rate": 0.041,
            "fed_funds_rate": 0.0475,
        },
    },
    {
        "category": "Economic Analysis",
        "subcategory": None,
        "title": "Sector Performance Heatmap 2025",
        "symbol": None,
        "access_level": "registered",
        "summary": "Year-to-date performance by GICS sector.",
        "tags": ["sectors", "performance"],
        "data": {
            "technology": 0.28,
            "healthcare": 0.12,
            "financials": 0.18,
            "energy": -0.05,
            "consumer_discretionary": 0.09,
        },
    },
    # ── Order Flow Analysis ────────────────────────────────────────────
    {
        "category": "Order Flow Analysis",
        "subcategory": None,
        "title": "ABC Corp Institutional Flow Q4 2025",
        "symbol": "ABC",
        "access_level": "premium",
        "summary": "Net institutional buying/selling pressure from 13F filings.",
        "tags": ["order-flow", "institutional", "ABC"],
        "data": {
            "net_institutional_flow": 12000000,
            "top_buyers": ["Vanguard", "BlackRock"],
            "top_sellers": ["Citadel"],
            "dark_pool_pct": 0.38,
        },
        "raw_data": {
            "quarterly_flows": {
                "Q1": 3000000,
                "Q2": 5000000,
                "Q3": -1000000,
                "Q4": 5000000,
            }
        },
    },
]


async def seed():
    db = await get_mongo_db()
    coll = db["reports"]

    # Clear existing seed data (idempotent re-run)
    await coll.delete_many({})
    print(f"Cleared existing reports")

    now = datetime.now(timezone.utc)
    for doc in SEED_REPORTS:
        doc.setdefault("created_at", now)
        doc.setdefault("updated_at", now)

    result = await coll.insert_many(SEED_REPORTS)
    print(f"Inserted {len(result.inserted_ids)} reports")

    # Verify count
    total = await coll.count_documents({})
    print(f"Verified: {total} reports in collection")

    # Verify folder tree
    from modules.reports.repository import get_folder_tree
    tree = await get_folder_tree(db)
    print("\nFolder tree:")
    for node in tree:
        print(f"  {node['name']} ({node['report_count']} reports)")
        for child in node.get("children", []):
            print(f"    └─ {child['name']} ({child['report_count']} reports)")

    await close_mongo()

    # Try to clear the running server's in-memory cache via API
    try:
        import urllib.request
        req = urllib.request.Request(
            "http://127.0.0.1:9000/reports/cache/clear",
            method="POST",
        )
        urllib.request.urlopen(req, timeout=3)
        print("\nServer cache cleared via API")
    except Exception:
        print("\nNote: Could not clear server cache (server might not be running or auth required).")
        print("  The server's in-memory cache will expire within 2 minutes.")

    print("\nSeed complete.")


if __name__ == "__main__":
    asyncio.run(seed())
