@echo off
echo ==========================================
echo   Setting up Company Legitimacy Pipeline
echo ==========================================

echo.
echo [1/2] Setting up Python Service...
pushd %~dp0\..
cd python_service

REM Check if venv exists
if not exist "venv" (
    echo    - Creating Virtual Environment...
    python -m venv venv
) else (
    echo    - Virtual Environment already exists.
)

REM Install dependencies
echo    - Installing dependencies...
.\venv\Scripts\python.exe -m pip install -r requirements.txt
echo    - Python Setup Complete.
cd ..

echo.
echo [2/2] Setting up Web Frontend (Next.js)...
cd web
echo    - Installing Node modules...
call npm install
echo    - Web Setup Complete.
cd ..

echo.
echo ==========================================
echo          SETUP COMPLETE 
echo ==========================================
echo To start the servers, run: start_dev.bat
pause
