const express = require('express');
const router = express.Router();

const {
    getAllReports,
    getCategories,
    getSymbols,
    getByCategory,
    getBySymbol,
    getReportById,
    getOverview,
} = require('../controllers/reportsController');

// ── Overview & Metadata ──────────────────────────────────────────────
router.get('/overview', getOverview);          // GET /api/reports/overview
router.get('/categories', getCategories);      // GET /api/reports/categories
router.get('/symbols', getSymbols);            // GET /api/reports/symbols

// ── Filtered Lists ───────────────────────────────────────────────────
router.get('/category/:category', getByCategory);  // GET /api/reports/category/Technical Analysis
router.get('/symbol/:symbol', getBySymbol);        // GET /api/reports/symbol/ABC

// ── Core CRUD ────────────────────────────────────────────────────────
router.get('/', getAllReports);                // GET /api/reports?category=...&symbol=...&page=1
router.get('/:id', getReportById);            // GET /api/reports/638a...

module.exports = router;
