# Autoservice Advanced Launch Script
$ErrorActionPreference = "Stop"

Clear-Host
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "   AUTOSERVICE MVP - STARTUP SYSTEM       " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 1. Start Docker Infrastructure
Write-Host "[1/4] Starting Docker infrastructure (DB and Redis)..." -ForegroundColor Yellow
try {
    docker-compose up -d db redis
    Write-Host "Docker services are up." -ForegroundColor Green
}
catch {
    Write-Host "Failed to start Docker. Please ensure Docker Desktop is running." -ForegroundColor Red
    exit
}

# 2. Start Backend
Write-Host "[2/4] Launching Backend (FastAPI)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\backend'; uvicorn app.main:app --reload --port 8000" -WindowStyle Normal

# 3. Start Telegram Bot
Write-Host "[3/4] Launching Telegram Bot..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\backend'; python bot_main.py" -WindowStyle Normal

# 4. Start Frontend
Write-Host "[4/4] Launching Frontend (Vite)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\frontend'; npm run dev" -WindowStyle Normal

# 5. Optional: Start Ngrok
if (Test-Path "ngrok.exe") {
    Write-Host "[BONUS] Launching Ngrok tunnel..." -ForegroundColor Magenta
    Start-Process cmd -ArgumentList "/k", "ngrok http 5173" -WindowStyle Normal
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "All services are launching!" -ForegroundColor Green
Write-Host "- API: http://localhost:8000"
Write-Host "- Web App: http://localhost:5173"
Write-Host "- Dashboard: http://localhost:5173/dashboard"
if (Test-Path "ngrok.exe") {
    Write-Host "- Ngrok: Check the separate CMD window for the public URL" -ForegroundColor Magenta
}
Write-Host "==========================================" -ForegroundColor Cyan

Write-Host ""
Write-Host "[TIP] Check the separate windows for logs." -ForegroundColor Gray
Write-Host "Press any key to close this launcher (services will stay running)..."
Read-Host
