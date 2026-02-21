const mongoose = require('mongoose');

const reportSchema = new mongoose.Schema({
    category: {
        type: String,
        required: true,
        trim: true,
        enum: [
            'Fundamental Analysis',
            'Technical Analysis',
            'Sentimental Analysis',
            'Economic Analysis',
            'Order Flow Analysis',
        ],
    },
    subcategory: {
        type: String,
        trim: true,
        default: null,
    },
    title: {
        type: String,
        required: true,
        trim: true,
    },
    symbol: {
        type: String,
        trim: true,
        default: null,
    },
    access_level: {
        type: String,
        enum: ['public', 'registered', 'premium'],
        default: 'public',
    },
    summary: {
        type: String,
        trim: true,
    },
    tags: {
        type: [String],
        default: [],
    },
    data: {
        type: mongoose.Schema.Types.Mixed,
        required: true,
    },
    raw_data: {
        type: mongoose.Schema.Types.Mixed,
        default: null,
    },
    methodology: {
        type: String,
        trim: true,
        default: null,
    },
    metadata: {
        type: mongoose.Schema.Types.Mixed,
        default: null,
    },
    created_at: {
        type: Date,
        default: Date.now,
    },
    updated_at: {
        type: Date,
        default: Date.now,
    },
});

// Indexes for common query patterns
reportSchema.index({ category: 1, subcategory: 1 });
reportSchema.index({ symbol: 1 });
reportSchema.index({ access_level: 1 });
reportSchema.index({ tags: 1 });

module.exports = mongoose.model('Report', reportSchema, 'reports');
