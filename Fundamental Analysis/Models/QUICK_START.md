# FD Extractor - Quick Start Guide

## Starting the Application

### 1. Start the Backend API (Terminal 1)

```bash
cd "Fundamental Analysis/Models/Ai Extractor"
python api_server.py
```

Or use the batch file (Windows):
```bash
start_api.bat
```

The API will start on `http://localhost:5000`

### 2. Start the Frontend (Terminal 2)

```bash
cd "Fundamental Analysis/Models/fdextractor"
npm run dev
```

Or use the batch file (Windows):
```bash
start_frontend.bat
```

The frontend will start on `http://localhost:3000`

### 3. Access the Application

Open your browser and navigate to: `http://localhost:3000`

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/pdfs` | GET | Get all PDFs |
| `/api/pdfs/by-category` | GET | Get PDFs grouped by category |
| `/api/pdfs/:pdfId/extract` | POST | Extract statements from PDF |
| `/api/pdfs/:pdfId/submit` | POST | Submit selected statements |
| `/api/categories` | GET | Get all categories |

## PDF Organization

PDFs should be organized in the `Ai Extractor/data/raw/` folder by category:

```
data/raw/
  ├── banks/
  │   ├── bank1_2023.pdf
  │   └── bank2_2023.pdf
  ├── commercial/
  │   └── company1_2023.pdf
  └── ...
```

Each folder name becomes a category in the dashboard.

## Troubleshooting

### Backend not starting
- Ensure Flask is installed: `pip install Flask Flask-CORS`
- Check if port 5000 is available
- Check Python path and dependencies

### Frontend not starting
- Ensure dependencies are installed: `npm install`
- Check if port 3000 is available
- Clear npm cache: `npm cache clean --force`

### No PDFs showing
- Check that PDFs exist in `Ai Extractor/data/raw/` folders
- Verify folder structure matches the expected format
- Check backend logs for errors

### API connection errors
- Verify both backend (5000) and frontend (3000) are running
- Check browser console for CORS or network errors
- Ensure proxy configuration in vite.config.js is correct
