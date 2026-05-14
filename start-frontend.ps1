# AgentCoolie Frontend Startup Script
# Run this from the project root directory.

$ErrorActionPreference = "Stop"

Write-Host "Starting AgentCoolie Frontend..." -ForegroundColor Green
Write-Host ""

if (-not (Test-Path -LiteralPath "package.json")) {
    Write-Host "Error: package.json not found!" -ForegroundColor Red
    Write-Host "Please run this script from the project root directory." -ForegroundColor Yellow
    exit 1
}

if (-not (Test-Path -LiteralPath "node_modules")) {
    Write-Host "Installing dependencies..." -ForegroundColor Cyan
    npm.cmd install
}

Write-Host ""
Write-Host "Starting Vite development server..." -ForegroundColor Green
Write-Host "Frontend running at: http://localhost:5173" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

npm.cmd run dev
