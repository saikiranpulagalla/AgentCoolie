# CoolieAssistant Backend Startup Script
# Run this from the project root directory

Write-Host "🚀 Starting CoolieAssistant Backend..." -ForegroundColor Green
Write-Host ""

# Check if we're in the right directory
if (-not (Test-Path "backend")) {
    Write-Host "❌ Error: backend directory not found!" -ForegroundColor Red
    Write-Host "Please run this script from the project root directory" -ForegroundColor Yellow
    exit 1
}

# Check if virtual environment exists
if (-not (Test-Path "backend\venv\Scripts\Activate.ps1")) {
    Write-Host "⚠️  Virtual environment not found. Creating one..." -ForegroundColor Yellow
    cd backend
    python -m venv venv
    cd ..
}

# Activate virtual environment
Write-Host "📦 Activating virtual environment..." -ForegroundColor Cyan
& "backend\venv\Scripts\Activate.ps1"

# Check if dependencies are installed
Write-Host "📚 Checking dependencies..." -ForegroundColor Cyan
cd backend
pip install -q -r requirements.txt 2>$null

# Start the server
Write-Host ""
Write-Host "✅ Starting Uvicorn server..." -ForegroundColor Green
Write-Host "📍 Backend running at: http://localhost:8000" -ForegroundColor Cyan
Write-Host "📖 API Docs at: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
