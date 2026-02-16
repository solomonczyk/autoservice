@echo off
echo Starting Autoservice Project...

start cmd /k "cd backend && venv\Scripts\activate && uvicorn app.main:app --reload"
start cmd /k "cd backend && venv\Scripts\activate && python bot_main.py"
start cmd /k "cd frontend && npm run dev"

echo All components are starting in separate windows.
pause
