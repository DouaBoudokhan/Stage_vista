@echo off
echo Starting StockIT Backend Server...
echo.

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Start server
uvicorn app.main:app --reload --reload-dir app --host 0.0.0.0 --port 8000
