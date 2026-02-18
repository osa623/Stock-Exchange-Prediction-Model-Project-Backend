# Stock Reports Node Backend

Standalone Express.js service that fetches financial report data from MongoDB (Azure CosmosDB).

## Quick Start

```bash
cd node-backend
npm install
npm run dev       # starts on http://127.0.0.1:9001
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/data/structure` | Hierarchical folder structure (Sector → Company → Year) |
| GET | `/api/data/:id` | Single report record by ID |

## Environment Variables

Copy `.env` and adjust as needed:

- `PORT` — server port (default: 9001)
- `MONGO_URI` — MongoDB/CosmosDB connection string
- `ALLOWED_ORIGINS` — comma-separated CORS origins
