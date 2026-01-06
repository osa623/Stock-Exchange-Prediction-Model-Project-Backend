@echo off
echo ============================================
echo  Financial Data Extractor - Quick Start
echo ============================================
echo.

echo [1/3] Checking Python environment...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

echo.
echo [2/3] Installing Python dependencies...
pip install -q flask flask-cors pdfplumber pandas openpyxl rapidfuzz PyMuPDF sentence-transformers

echo.
echo [3/3] Starting API Server...
echo Server will start on http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo.

python api_server.py

pause
