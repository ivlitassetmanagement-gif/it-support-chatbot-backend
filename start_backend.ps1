#!/usr/bin/env pwsh

$ErrorActionPreference = "Continue"

Write-Host "Starting IT Support Chatbot Backend..." -ForegroundColor Cyan

# Navigate to backend directory - IMPORTANT: Must be here for .env to load
$backendDir = "D:\IT_Support_Chatbot\backend"
cd $backendDir
Write-Host "Working directory: $(Get-Location)" -ForegroundColor Gray

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "ERROR: .env file not found in backend directory" -ForegroundColor Red
    exit 1
}

Write-Host ".env file found" -ForegroundColor Green

# Activate venv
$venvPath = ".\venv\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    Write-Host "Activating virtual environment..." -ForegroundColor Green
    & $venvPath
} else {
    Write-Host "ERROR: Virtual environment not found at $venvPath" -ForegroundColor Red
    exit 1
}

# Start the backend from backend directory (NOT app directory)
# Uvicorn will find main:app correctly since we're in backend/app/main.py
Write-Host "Starting FastAPI server on port 8001..." -ForegroundColor Green
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Backend failed to start (exit code: $LASTEXITCODE)" -ForegroundColor Red
    exit 1
}
