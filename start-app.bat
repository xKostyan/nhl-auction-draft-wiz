@echo off
setlocal EnableDelayedExpansion

set SCRIPT_DIR=%~dp0
set APP_PORT=8050
set VENV_DIR=%SCRIPT_DIR%.venv
set ACTION=%1
if "%ACTION%"=="" set ACTION=start

if /I "%ACTION%"=="start" (
    if not exist "%VENV_DIR%\Scripts\python.exe" (
        echo Missing local virtual environment: %VENV_DIR%
        echo Create it with: py -m venv .venv
        echo Then install deps with: .venv\Scripts\activate && python -m pip install -r requirements.txt
        exit /b 1
    )

    start "NHL Auction Draft Wiz" cmd /k "cd /d "%SCRIPT_DIR%" && call .venv\Scripts\activate.bat && python app.py"
    echo Started NHL Auction Draft Wiz in a separate terminal window.
    exit /b 0
)

if /I "%ACTION%"=="stop" (
    for /f "skip=1 tokens=5" %%P in ('netstat -ano ^| findstr :%APP_PORT%') do (
        set PID=%%P
        taskkill /PID !PID! /F >nul 2>&1
        echo Stopped process PID !PID!
    )
    exit /b 0
)

echo Usage: %~nx0 [start^|stop]
echo Examples:
echo   %~nx0 start
echo   %~nx0 stop
exit /b 1
