#!/bin/bash

echo "========================================"
echo "   Candy AI Clone - Startup Script"
echo "========================================"
echo

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "[ERROR] Docker is not running. Please start Docker."
    exit 1
fi

echo "[1/4] Starting PostgreSQL and Redis containers..."
docker-compose up -d

echo
echo "[2/4] Waiting for databases to be ready..."
sleep 10

echo
echo "[3/4] Installing Python dependencies..."
cd backend
pip install -r requirements.txt

echo
echo "[4/4] Starting FastAPI server..."
echo
echo "========================================"
echo "   Server starting at http://localhost:8000"
echo "   API docs at http://localhost:8000/docs"
echo "========================================"
echo

python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
