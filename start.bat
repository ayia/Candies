@echo off
echo ========================================
echo    Candy AI Clone - Startup Script
echo ========================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not running. Please start Docker Desktop.
    pause
    exit /b 1
)

echo [1/4] Starting PostgreSQL and Redis containers...
docker-compose up -d

echo.
echo [2/4] Waiting for databases to be ready...
timeout /t 10 /nobreak >nul

echo.
echo [3/4] Installing Python dependencies...
cd backend
pip install -r requirements.txt

echo.
echo [4/4] Starting FastAPI server...
echo.
echo ========================================
echo    Server starting at http://localhost:8000
echo    API docs at http://localhost:8000/docs
echo ========================================
echo.

python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
