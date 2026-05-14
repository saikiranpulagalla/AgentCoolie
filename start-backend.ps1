# AgentCoolie Backend Startup Script
# Run this from the project root directory.

$ErrorActionPreference = "Stop"

Write-Host "Starting AgentCoolie Backend..." -ForegroundColor Green
Write-Host ""

if (-not (Test-Path -LiteralPath "backend")) {
    Write-Host "Error: backend directory not found!" -ForegroundColor Red
    Write-Host "Please run this script from the project root directory." -ForegroundColor Yellow
    exit 1
}

$venvPython = "backend\venv\Scripts\python.exe"
$venvOk = $false

if (Test-Path -LiteralPath $venvPython) {
    try {
        & $venvPython --version | Out-Null
        $venvOk = $true
    }
    catch {
        $venvOk = $false
    }
}

if (-not $venvOk) {
    Write-Host "Virtual environment not found. Creating one..." -ForegroundColor Yellow
    if (Test-Path -LiteralPath "backend\venv") {
        Remove-Item -LiteralPath "backend\venv" -Recurse -Force
    }
    py -m venv backend\venv
}

Write-Host "Checking dependencies..." -ForegroundColor Cyan
Push-Location backend
try {
    .\venv\Scripts\python.exe -m pip install -q -r requirements.txt

    Write-Host ""
    Write-Host "Starting Uvicorn server..." -ForegroundColor Green
    Write-Host "Backend running at: http://localhost:8000" -ForegroundColor Cyan
    Write-Host "API Docs at: http://localhost:8000/docs" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
    Write-Host ""

    .\venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
}
finally {
    Pop-Location
}
