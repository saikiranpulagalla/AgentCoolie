#!/bin/bash

# CoolieAssistant Backend Startup Script
# Run this from the project root directory

echo "🚀 Starting CoolieAssistant Backend..."
echo ""

# Check if we're in the right directory
if [ ! -d "backend" ]; then
    echo "❌ Error: backend directory not found!"
    echo "Please run this script from the project root directory"
    exit 1
fi

# Check if virtual environment exists
if [ ! -f "backend/venv/bin/activate" ]; then
    echo "⚠️  Virtual environment not found. Creating one..."
    cd backend
    python3 -m venv venv
    cd ..
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source backend/venv/bin/activate

# Check if dependencies are installed
echo "📚 Checking dependencies..."
cd backend
pip install -q -r requirements.txt 2>/dev/null

# Start the server
echo ""
echo "✅ Starting Uvicorn server..."
echo "📍 Backend running at: http://localhost:8000"
echo "📖 API Docs at: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
