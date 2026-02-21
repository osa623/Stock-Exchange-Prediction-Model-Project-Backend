/**
 * Seed script — populates MongoDB 'reports' collection with sample data.
 *
 * Usage:
 *   cd node-backend
 *   npm run seed
 */

require("dotenv").config();
const mongoose = require("mongoose");
const connectDB = require("./config/db");

const now = new Date();

const SEED_REPORTS = [
  // ── Fundamental Analysis / Ratios ──────────────────────────────────
  {
    category: "Fundamental Analysis",
    subcategory: "Ratios",
    title: "ABC Corp Ratio Analysis 2024",
    symbol: "ABC",
    access_level: "public",
    summary: "Key valuation ratios for ABC Corp covering PE, PB, PS, EV/EBITDA, ROE, and ROA for fiscal year 2024.",
    tags: ["ratios", "valuation", "ABC"],
    data: { pe_ratio: 15.2, pb_ratio: 2.1, ps_ratio: 1.8, ev_ebitda: 10.5, roe: 0.18, roa: 0.09, eps: 3.45, dividend_yield: 0.025 },
    raw_data: { yearly: { "2022": { pe: 14.1, pb: 1.9, roe: 0.16 }, "2023": { pe: 14.8, pb: 2.0, roe: 0.17 }, "2024": { pe: 15.2, pb: 2.1, roe: 0.18 } } },
    methodology: "Ratios computed from audited annual statements using standard formulas.",
    created_at: now, updated_at: now,
  },
  {
    category: "Fundamental Analysis",
    subcategory: "Ratios",
    title: "XYZ Inc Ratio Analysis 2024",
    symbol: "XYZ",
    access_level: "registered",
    summary: "Comprehensive ratio set for XYZ Inc — profitability, liquidity, and leverage.",
    tags: ["ratios", "XYZ", "profitability"],
    data: { pe_ratio: 22.6, pb_ratio: 4.3, current_ratio: 1.8, debt_to_equity: 0.45, roe: 0.24, roa: 0.12 },
    created_at: now, updated_at: now,
  },
  // ── Fundamental Analysis / Valuation ───────────────────────────────
  {
    category: "Fundamental Analysis",
    subcategory: "Valuation",
    title: "ABC Corp DCF Valuation",
    symbol: "ABC",
    access_level: "premium",
    summary: "Discounted Cash Flow valuation with 10-year projection and terminal value.",
    tags: ["dcf", "valuation", "ABC"],
    data: { intrinsic_price: 52.30, current_price: 48.00, margin_of_safety: 0.082, safe_buy_price: 44.60, wacc: 0.095, terminal_growth: 0.025 },
    raw_data: { projected_fcf: [5.2, 5.8, 6.3, 6.9, 7.4, 7.9, 8.3, 8.7, 9.1, 9.5], terminal_value: 142.5 },
    methodology: "Two-stage DCF with WACC discount rate, Gordon Growth terminal value.",
    metadata: { model_version: "2.1", analyst: "system", confidence: "medium" },
    created_at: now, updated_at: now,
  },
  {
    category: "Fundamental Analysis",
    subcategory: "Valuation",
    title: "XYZ Inc Gordon Growth Model",
    symbol: "XYZ",
    access_level: "registered",
    summary: "Dividend discount model using Gordon Growth for stable-dividend payers.",
    tags: ["ddm", "gordon", "XYZ", "dividends"],
    data: { intrinsic_price: 38.50, current_price: 35.00, dividend_per_share: 1.20, required_return: 0.10, growth_rate: 0.04 },
    created_at: now, updated_at: now,
  },
  // ── Fundamental Analysis / Calculations ────────────────────────────
  {
    category: "Fundamental Analysis",
    subcategory: "Calculations",
    title: "ABC Corp Income Statement Analysis",
    symbol: "ABC",
    access_level: "public",
    summary: "Revenue growth, gross/operating/net margins, EBITDA, and earnings quality metrics.",
    tags: ["income", "margins", "ABC"],
    data: { revenue_growth: 0.12, gross_margin: 0.42, operating_margin: 0.18, net_margin: 0.11, ebitda: 25000000, earnings_quality_score: 0.85 },
    created_at: now, updated_at: now,
  },
  {
    category: "Fundamental Analysis",
    subcategory: "Calculations",
    title: "ABC Corp Cash Flow Analysis",
    symbol: "ABC",
    access_level: "registered",
    summary: "Free cash flow, cash conversion ratio, and cash flow adequacy assessment.",
    tags: ["cashflow", "fcf", "ABC"],
    data: { free_cash_flow: 15000000, fcf_per_share: 3.00, cash_conversion_ratio: 0.92, ocf_margin: 0.22, capex_ratio: 0.08 },
    created_at: now, updated_at: now,
  },
  {
    category: "Fundamental Analysis",
    subcategory: "Calculations",
    title: "ABC Corp Balance Sheet Health",
    symbol: "ABC",
    access_level: "premium",
    summary: "Working capital, current/quick ratios, debt structure, and capital preservation.",
    tags: ["balance-sheet", "liquidity", "ABC"],
    data: { current_ratio: 2.1, quick_ratio: 1.5, cash_ratio: 0.8, debt_to_equity: 0.35, net_debt: 12000000, working_capital: 30000000 },
    raw_data: { yearly: { "2022": { current_ratio: 1.9, debt_eq: 0.40 }, "2023": { current_ratio: 2.0, debt_eq: 0.38 }, "2024": { current_ratio: 2.1, debt_eq: 0.35 } } },
    created_at: now, updated_at: now,
  },
  // ── Fundamental Analysis / Forecasting ─────────────────────────────
  {
    category: "Fundamental Analysis",
    subcategory: "Forecasting",
    title: "ABC Corp Revenue Forecast 2025-2027",
    symbol: "ABC",
    access_level: "premium",
    summary: "Three-year revenue forecast using regression + seasonal adjustment.",
    tags: ["forecast", "revenue", "ABC"],
    data: { forecast_2025: 280000000, forecast_2026: 310000000, forecast_2027: 340000000, cagr: 0.10, confidence_interval: "80%" },
    methodology: "Linear regression on 5Y trailing revenue with seasonal decomposition.",
    created_at: now, updated_at: now,
  },
  // ── Technical Analysis ─────────────────────────────────────────────
  {
    category: "Technical Analysis",
    subcategory: null,
    title: "ABC Corp Moving Average Crossover",
    symbol: "ABC",
    access_level: "public",
    summary: "50/200 day moving average crossover signal analysis.",
    tags: ["technical", "moving-average", "ABC"],
    data: { ma_50: 47.50, ma_200: 45.80, signal: "bullish_crossover", signal_date: "2025-12-15" },
    created_at: now, updated_at: now,
  },
  {
    category: "Technical Analysis",
    subcategory: null,
    title: "XYZ Inc RSI & MACD Analysis",
    symbol: "XYZ",
    access_level: "registered",
    summary: "Relative Strength Index and MACD divergence assessment.",
    tags: ["technical", "rsi", "macd", "XYZ"],
    data: { rsi_14: 62.3, macd_signal: "neutral", macd_histogram: 0.15 },
    created_at: now, updated_at: now,
  },
  // ── Sentimental Analysis ───────────────────────────────────────────
  {
    category: "Sentimental Analysis",
    subcategory: null,
    title: "ABC Corp News Sentiment Q4 2025",
    symbol: "ABC",
    access_level: "public",
    summary: "Aggregated news sentiment score from 150+ articles.",
    tags: ["sentiment", "news", "ABC"],
    data: { sentiment_score: 0.72, articles_analyzed: 153, positive_pct: 0.65, negative_pct: 0.12, neutral_pct: 0.23 },
    created_at: now, updated_at: now,
  },
  // ── Economic Analysis ──────────────────────────────────────────────
  {
    category: "Economic Analysis",
    subcategory: null,
    title: "Macro Economic Indicators Q4 2025",
    symbol: null,
    access_level: "public",
    summary: "GDP growth, inflation, unemployment, and interest rate trends.",
    tags: ["macro", "gdp", "inflation"],
    data: { gdp_growth: 0.023, cpi_inflation: 0.031, unemployment_rate: 0.041, fed_funds_rate: 0.0475 },
    created_at: now, updated_at: now,
  },
  {
    category: "Economic Analysis",
    subcategory: null,
    title: "Sector Performance Heatmap 2025",
    symbol: null,
    access_level: "registered",
    summary: "Year-to-date performance by GICS sector.",
    tags: ["sectors", "performance"],
    data: { technology: 0.28, healthcare: 0.12, financials: 0.18, energy: -0.05, consumer_discretionary: 0.09 },
    created_at: now, updated_at: now,
  },
  // ── Order Flow Analysis ────────────────────────────────────────────
  {
    category: "Order Flow Analysis",
    subcategory: null,
    title: "ABC Corp Institutional Flow Q4 2025",
    symbol: "ABC",
    access_level: "premium",
    summary: "Net institutional buying/selling pressure from 13F filings.",
    tags: ["order-flow", "institutional", "ABC"],
    data: { net_institutional_flow: 12000000, top_buyers: ["Vanguard", "BlackRock"], top_sellers: ["Citadel"], dark_pool_pct: 0.38 },
    raw_data: { quarterly_flows: { Q1: 3000000, Q2: 5000000, Q3: -1000000, Q4: 5000000 } },
    created_at: now, updated_at: now,
  },
];

async function seed() {
  await connectDB();
  const db = mongoose.connection.db;
  const coll = db.collection("reports");

  await coll.deleteMany({});
  console.log("Cleared existing reports");

  const result = await coll.insertMany(SEED_REPORTS);
  console.log(`Inserted ${result.insertedCount} reports`);

  const total = await coll.countDocuments({});
  console.log(`Verified: ${total} reports in collection`);

  await mongoose.connection.close();
  console.log("\nSeed complete.");
}

seed().catch((err) => {
  console.error("Seed failed:", err);
  process.exit(1);
});
