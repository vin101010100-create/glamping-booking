@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv .venv
    call ".venv\Scripts\activate.bat"
    python -m pip install -r requirements.txt
) else (
    call ".venv\Scripts\activate.bat"
)

if not exist "instance\glamping.db" (
    echo Preparing database...
    flask --app run.py db upgrade
    flask --app run.py seed-db
)

echo.
echo Starting Sakha Glamping at http://127.0.0.1:5000
echo Press Ctrl+C to stop the server.
echo.
start "" /b cmd /c "timeout /t 2 >nul & start http://127.0.0.1:5000"
flask --app run.py run --debug
pause
