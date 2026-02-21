const Report = require('../models/report');

/**
 * GET /api/reports
 * Fetch all reports with optional query filters.
 *
 * Query params:
 *   category     – filter by category (exact match)
 *   subcategory  – filter by subcategory
 *   symbol       – filter by stock symbol (case-insensitive)
 *   access_level – filter by access level (public | registered | premium)
 *   tag          – filter by tag (reports containing this tag)
 *   search       – text search across title & summary
 *   page         – page number (default 1)
 *   limit        – items per page (default 50, max 200)
 *   sort         – field to sort by (default: created_at)
 *   order        – asc | desc (default: desc)
 */
exports.getAllReports = async (req, res) => {
    try {
        const {
            category,
            subcategory,
            symbol,
            access_level,
            tag,
            search,
            page = 1,
            limit = 50,
            sort = 'created_at',
            order = 'desc',
        } = req.query;

        const filter = {};

        if (category) filter.category = category;
        if (subcategory) filter.subcategory = subcategory;
        if (symbol) filter.symbol = { $regex: new RegExp(`^${symbol}$`, 'i') };
        if (access_level) filter.access_level = access_level;
        if (tag) filter.tags = tag;
        if (search) {
            filter.$or = [
                { title: { $regex: search, $options: 'i' } },
                { summary: { $regex: search, $options: 'i' } },
            ];
        }

        const pageNum = Math.max(1, parseInt(page, 10) || 1);
        const limitNum = Math.min(200, Math.max(1, parseInt(limit, 10) || 50));
        const skip = (pageNum - 1) * limitNum;
        const sortOrder = order === 'asc' ? 1 : -1;

        const [reports, total] = await Promise.all([
            Report.find(filter)
                .sort({ [sort]: sortOrder })
                .skip(skip)
                .limit(limitNum)
                .lean(),
            Report.countDocuments(filter),
        ]);

        res.json({
            success: true,
            data: reports,
            pagination: {
                page: pageNum,
                limit: limitNum,
                total,
                totalPages: Math.ceil(total / limitNum),
            },
        });
    } catch (error) {
        console.error('getAllReports Error:', error);
        res.status(500).json({ success: false, error: 'Failed to fetch reports' });
    }
};

/**
 * GET /api/reports/categories
 * Returns the list of unique categories with counts.
 */
exports.getCategories = async (_req, res) => {
    try {
        const categories = await Report.aggregate([
            { $group: { _id: '$category', count: { $sum: 1 } } },
            { $sort: { _id: 1 } },
            { $project: { _id: 0, category: '$_id', count: 1 } },
        ]);
        res.json({ success: true, data: categories });
    } catch (error) {
        console.error('getCategories Error:', error);
        res.status(500).json({ success: false, error: 'Failed to fetch categories' });
    }
};

/**
 * GET /api/reports/symbols
 * Returns unique stock symbols present in reports.
 */
exports.getSymbols = async (_req, res) => {
    try {
        const symbols = await Report.aggregate([
            { $match: { symbol: { $ne: null } } },
            { $group: { _id: '$symbol', count: { $sum: 1 } } },
            { $sort: { _id: 1 } },
            { $project: { _id: 0, symbol: '$_id', count: 1 } },
        ]);
        res.json({ success: true, data: symbols });
    } catch (error) {
        console.error('getSymbols Error:', error);
        res.status(500).json({ success: false, error: 'Failed to fetch symbols' });
    }
};

/**
 * GET /api/reports/category/:category
 * Fetch reports by category, optionally filtered by subcategory.
 */
exports.getByCategory = async (req, res) => {
    try {
        const { category } = req.params;
        const { subcategory } = req.query;

        const filter = { category };
        if (subcategory) filter.subcategory = subcategory;

        const reports = await Report.find(filter).sort({ created_at: -1 }).lean();
        res.json({ success: true, data: reports, total: reports.length });
    } catch (error) {
        console.error('getByCategory Error:', error);
        res.status(500).json({ success: false, error: 'Failed to fetch reports by category' });
    }
};

/**
 * GET /api/reports/symbol/:symbol
 * Fetch all reports for a specific stock symbol.
 */
exports.getBySymbol = async (req, res) => {
    try {
        const { symbol } = req.params;
        const reports = await Report.find({
            symbol: { $regex: new RegExp(`^${symbol}$`, 'i') },
        })
            .sort({ created_at: -1 })
            .lean();

        res.json({ success: true, data: reports, total: reports.length });
    } catch (error) {
        console.error('getBySymbol Error:', error);
        res.status(500).json({ success: false, error: 'Failed to fetch reports by symbol' });
    }
};

/**
 * GET /api/reports/:id
 * Fetch a single report by MongoDB ObjectId.
 */
exports.getReportById = async (req, res) => {
    try {
        const { id } = req.params;
        const report = await Report.findById(id).lean();

        if (!report) {
            return res.status(404).json({ success: false, error: 'Report not found' });
        }

        res.json({ success: true, data: report });
    } catch (error) {
        console.error('getReportById Error:', error);
        res.status(500).json({ success: false, error: 'Failed to fetch report' });
    }
};

/**
 * GET /api/reports/overview
 * Returns a high-level overview: counts per category & per access_level.
 */
exports.getOverview = async (_req, res) => {
    try {
        const [byCategory, byAccess, total] = await Promise.all([
            Report.aggregate([
                { $group: { _id: '$category', count: { $sum: 1 } } },
                { $sort: { _id: 1 } },
            ]),
            Report.aggregate([
                { $group: { _id: '$access_level', count: { $sum: 1 } } },
                { $sort: { _id: 1 } },
            ]),
            Report.countDocuments(),
        ]);

        res.json({
            success: true,
            data: {
                total,
                byCategory: byCategory.map((c) => ({ category: c._id, count: c.count })),
                byAccessLevel: byAccess.map((a) => ({ access_level: a._id, count: a.count })),
            },
        });
    } catch (error) {
        console.error('getOverview Error:', error);
        res.status(500).json({ success: false, error: 'Failed to fetch overview' });
    }
};
