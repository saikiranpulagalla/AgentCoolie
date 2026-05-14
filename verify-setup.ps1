# AgentCoolie Setup Verification Script
# Checks if everything is configured correctly

Write-Host "Verifying AgentCoolie Setup..." -ForegroundColor Green
Write-Host ""

$errors = @()
$warnings = @()

# Check Python
Write-Host "Checking Python..." -ForegroundColor Cyan
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  $pythonVersion" -ForegroundColor Green
} catch {
    $errors += "Python not found. Install from https://python.org/"
}

# Check Node.js
Write-Host "Checking Node.js..." -ForegroundColor Cyan
try {
    $nodeVersion = node --version 2>&1
    Write-Host "  $nodeVersion" -ForegroundColor Green
} catch {
    $errors += "Node.js not found. Install from https://nodejs.org/"
}

# Check npm
Write-Host "Checking npm..." -ForegroundColor Cyan
try {
    $npmVersion = npm --version 2>&1
    Write-Host "  npm $npmVersion" -ForegroundColor Green
} catch {
    $errors += "npm not found"
}

# Check backend directory
Write-Host "Checking backend directory..." -ForegroundColor Cyan
if (Test-Path "backend") {
    Write-Host "  backend/ found" -ForegroundColor Green
} else {
    $errors += "backend/ directory not found"
}

# Check client directory
Write-Host "Checking client directory..." -ForegroundColor Cyan
if (Test-Path "client") {
    Write-Host "  client/ found" -ForegroundColor Green
} else {
    $errors += "client/ directory not found"
}

# Check .env file
Write-Host "Checking .env file..." -ForegroundColor Cyan
if (Test-Path ".env") {
    Write-Host "  .env found" -ForegroundColor Green
    
    $envContent = Get-Content ".env" -Raw
    
    if ($envContent -like "*VITE_FIREBASE_API_KEY*") {
        Write-Host "    VITE_FIREBASE_API_KEY set" -ForegroundColor Green
    } else {
        $warnings += "VITE_FIREBASE_API_KEY not set in .env"
    }
    
    if ($envContent -like "*SUPABASE_URL*") {
        Write-Host "    SUPABASE_URL set" -ForegroundColor Green
    } else {
        $warnings += "SUPABASE_URL not set in .env"
    }
    
    if ($envContent -like "*GOOGLE_AI_API_KEY*") {
        Write-Host "    GOOGLE_AI_API_KEY set" -ForegroundColor Green
    } else {
        $warnings += "GOOGLE_AI_API_KEY not set in .env"
    }
} else {
    $errors += ".env file not found. Copy from .env.example"
}

# Check requirements.txt
Write-Host "Checking requirements.txt..." -ForegroundColor Cyan
if (Test-Path "backend/requirements.txt") {
    Write-Host "  backend/requirements.txt found" -ForegroundColor Green
} else {
    $errors += "backend/requirements.txt not found"
}

# Check package.json
Write-Host "Checking package.json..." -ForegroundColor Cyan
if (Test-Path "package.json") {
    Write-Host "  package.json found" -ForegroundColor Green
} else {
    $errors += "package.json not found"
}

# Check startup scripts
Write-Host "Checking startup scripts..." -ForegroundColor Cyan
if (Test-Path "start-backend.ps1") {
    Write-Host "  start-backend.ps1 found" -ForegroundColor Green
} else {
    $warnings += "start-backend.ps1 not found"
}

if (Test-Path "start-frontend.ps1") {
    Write-Host "  start-frontend.ps1 found" -ForegroundColor Green
} else {
    $warnings += "start-frontend.ps1 not found"
}

Write-Host ""
Write-Host "=================================================="

if ($errors.Count -eq 0 -and $warnings.Count -eq 0) {
    Write-Host "All checks passed! Ready to start." -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Run: .\start-backend.ps1" -ForegroundColor White
    Write-Host "2. In another terminal: .\start-frontend.ps1" -ForegroundColor White
    Write-Host "3. Open: http://localhost:5173" -ForegroundColor White
} else {
    if ($errors.Count -gt 0) {
        Write-Host "Errors found:" -ForegroundColor Red
        foreach ($error in $errors) {
            Write-Host "  - $error" -ForegroundColor Red
        }
        Write-Host ""
    }
    
    if ($warnings.Count -gt 0) {
        Write-Host "Warnings:" -ForegroundColor Yellow
        foreach ($warning in $warnings) {
            Write-Host "  - $warning" -ForegroundColor Yellow
        }
        Write-Host ""
    }
    
    Write-Host "Please fix the issues above before starting." -ForegroundColor Yellow
}

Write-Host "=================================================="
