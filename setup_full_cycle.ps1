# Autoservice Full Cycle Test Setup
$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "   AUTOSERVICE - FULL CYCLE SETUP         " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 1. Start Docker (DB & Redis)
Write-Host "`n[1/5] Checking Docker Infrastructure..." -ForegroundColor Yellow
try {
    docker-compose up -d db redis
    Write-Host "✔ Docker services are up." -ForegroundColor Green
}
catch {
    Write-Host "✖ Failed to start Docker. Please ensure Docker Desktop is running." -ForegroundColor Red
    exit
}

# 2. Wait for DB (Simple pause)
Write-Host "`n[2/5] Waiting for Database to be ready (5s)..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# 3. Run Migrations & Seed Data
Write-Host "`n[3/5] Protecting Database Schema & Seeding Data..." -ForegroundColor Yellow
$BackendDir = Join-Path $PSScriptRoot "backend"
Push-Location $BackendDir

# Activate Venv if exists
if (Test-Path "venv") {
    . .\venv\Scripts\Activate.ps1
}

# Run Alembic
Write-Host "Running Alembic Migrations..." -ForegroundColor Gray
alembic upgrade head

# Run Seeding
Write-Host "Seeding Data..." -ForegroundColor Gray
python seed_data.py

Pop-Location

# 4. Handle Ngrok & .env
Write-Host "`n[4/5] Configuring Network (Ngrok)..." -ForegroundColor Yellow
if (Get-Process ngrok -ErrorAction SilentlyContinue) {
    Write-Host "Ngrok is already running." -ForegroundColor Gray
}
else {
    if (Test-Path "ngrok.exe") {
        Write-Host "Starting Ngrok..." -ForegroundColor Gray
        Start-Process -FilePath "ngrok.exe" -ArgumentList "http 5173" -WindowStyle Minimized
        Write-Host "Waiting for Ngrok tunnel..." -ForegroundColor Gray
        Start-Sleep -Seconds 5
    }
    else {
        Write-Host "⚠ Ngrok executable not found in root. Skipping tunnel setup." -ForegroundColor Red
    }
}

# Try to fetch Ngrok URL
try {
    $ngrokTunnels = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels" -ErrorAction Stop
    $publicUrl = $ngrokTunnels.tunnels[0].public_url
    
    if ($publicUrl) {
        Write-Host "✔ Ngrok Tunnel: $publicUrl" -ForegroundColor Green
        
        # Update .env
        $EnvFile = Join-Path $BackendDir ".env"
        $EnvContent = Get-Content $EnvFile
        $NewEnvContent = $EnvContent | ForEach-Object {
            if ($_ -match "^WEBAPP_URL=") {
                "WEBAPP_URL=$publicUrl/webapp"
            }
            else {
                $_
            }
        }
        $NewEnvContent | Set-Content $EnvFile
        Write-Host "✔ Updated .env with new WEBAPP_URL" -ForegroundColor Green
    }
}
catch {
    Write-Host "⚠ Could not fetch Ngrok URL. Is Ngrok running?" -ForegroundColor Red
}

Write-Host "`n[5/5] Ready for Launch!" -ForegroundColor Cyan
Write-Host "1. Run '.\run_all.ps1' to start Backend, Frontend, and Bot."
Write-Host "2. Open Telegram and start the bot."
Write-Host "3. Open http://localhost:5173/dashboard to see the Kanban board."
Write-Host "==========================================" -ForegroundColor Cyan
