@echo off
setlocal
title TelScope OSINT Framework

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Python 3.10+ not found on PATH. Install Python first.
    pause
    exit /b 1
)

echo [*] Setting up local virtual environment...
if not exist venv (
    python -m venv venv
)
call venv\Scripts\activate.bat

echo [*] Ensuring dependencies...
pip install -r requirements.txt --quiet --disable-pip-version-check

echo [*] Provisioning pinned tools (first run only, internet needed once)...
python bootstrap.py
if %errorlevel% neq 0 echo [!] bootstrap reported problems - continuing (modules may show unavailable)

echo [*] Starting TelScope on http://127.0.0.1:8000 ...
start "" http://127.0.0.1:8000
python app.py
pause
