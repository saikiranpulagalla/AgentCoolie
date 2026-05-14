# AgentCoolie Complete Startup Script
# Starts both backend and frontend in separate windows.

Write-Host "Starting AgentCoolie (Backend + Frontend)..." -ForegroundColor Green
Write-Host ""

if (-not (Test-Path -LiteralPath "backend") -or -not (Test-Path -LiteralPath "client")) {
    Write-Host "Error: backend or client directory not found!" -ForegroundColor Red
    Write-Host "Please run this script from the project root directory." -ForegroundColor Yellow
    exit 1
}

Write-Host "Starting backend in a new window..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "& '.\start-backend.ps1'"

Write-Host "Waiting 3 seconds for backend to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

Write-Host "Starting frontend in a new window..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "& '.\start-frontend.ps1'"

Write-Host ""
Write-Host "Both services are starting." -ForegroundColor Green
Write-Host ""
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Cyan
Write-Host "Backend: http://localhost:8000" -ForegroundColor Cyan
Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Check the new windows for detailed output." -ForegroundColor Yellow
