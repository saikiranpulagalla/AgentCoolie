#!/bin/bash

# AgentCoolie Backend Startup Script
# Run this from the project root directory.

echo "Starting AgentCoolie Backend..."
echo ""

if [ ! -d "backend" ]; then
    echo "Error: backend directory not found!"
    echo "Please run this script from the project root directory."
    exit 1
fi

if [ ! -f "backend/venv/bin/activate" ]; then
    echo "Virtual environment not found. Creating one..."
    cd backend
    python3 -m venv venv
    cd ..
fi

echo "Activating virtual environment..."
source backend/venv/bin/activate

echo "Checking dependencies..."
cd backend
pip install -q -r requirements.txt 2>/dev/null

echo ""
echo "Starting Uvicorn server..."
echo "Backend running at: http://localhost:8000"
echo "API Docs at: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
