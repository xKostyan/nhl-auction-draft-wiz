@echo off
setlocal EnableDelayedExpansion

set SCRIPT_DIR=%~dp0
set APP_PORT=8050
set ACTION=%1
if "%ACTION%"=="" set ACTION=start

if /I "%ACTION%"=="start" (
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
