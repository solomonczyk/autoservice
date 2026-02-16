# Autoservice Launch Script

Write-Host "Starting Autoservice Project components..." -ForegroundColor Cyan

# Start Backend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; if (Test-Path venv) { .\venv\Scripts\Activate.ps1 }; uvicorn app.main:app --reload" -WindowStyle Normal

# Start Bot
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; if (Test-Path venv) { .\venv\Scripts\Activate.ps1 }; python bot_main.py" -WindowStyle Normal

# Start Frontend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev" -WindowStyle Normal

Write-Host "Backend, Bot, and Frontend are launching in separate windows." -ForegroundColor Green
Write-Host "Press any key to exit this launcher..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
