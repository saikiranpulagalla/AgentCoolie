# CoolieAssistant Frontend Startup Script
# Run this from the project root directory

Write-Host "🚀 Starting CoolieAssistant Frontend..." -ForegroundColor Green
Write-Host ""

# Check if we're in the right directory
if (-not (Test-Path "client")) {
    Write-Host "❌ Error: client directory not found!" -ForegroundColor Red
    Write-Host "Please run this script from the project root directory" -ForegroundColor Yellow
    exit 1
}

# Check if node_modules exists
if (-not (Test-Path "client\node_modules")) {
    Write-Host "📦 Installing dependencies..." -ForegroundColor Cyan
    cd client
    npm install
    cd ..
}

# Start the development server
Write-Host ""
Write-Host "✅ Starting Vite development server..." -ForegroundColor Green
Write-Host "📍 Frontend running at: http://localhost:5173" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

cd client
npm run dev
