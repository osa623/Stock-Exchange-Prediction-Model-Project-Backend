const express = require('express');
const cors = require('cors');
const path = require('path');
const dotenv = require('dotenv');

dotenv.config({ path: path.resolve(__dirname, '..', '.env') });

const connectDB = require('./config/db');
const dataRoutes = require('./routes/reportRoute');
const reportsRoutes = require('./routes/reportsRoute');

// Connect to MongoDB
connectDB();

const app = express();
const PORT = process.env.PORT || 9001;

app.use(cors({
    origin: (process.env.ALLOWED_ORIGINS || "http://localhost:3001")
        .split(",")
        .map(s => s.trim())
        .filter(Boolean),
    credentials: true
}));
app.use(express.json());

// Simple request logger
app.use((req, _res, next) => {
    console.log(`[${new Date().toISOString()}] ${req.method} ${req.path}`);
    next();
});

// Routes
app.use('/api/data', dataRoutes);
app.use('/api/reports', reportsRoutes);

app.get('/', (_req, res) => {
    res.json({
        service: 'Stock Reports Node Backend',
        version: '1.0.0',
        status: 'running',
    });
});

// Global error handler
app.use((err, _req, res, _next) => {
    console.error('[error]', err.message || err);
    res.status(500).json({ error: 'Internal server error' });
});

app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
