@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "VENV_DIR=%SCRIPT_DIR%.venv"

where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set "PYTHON=py -3"
) else (
    where python >nul 2>&1
    if not %ERRORLEVEL% EQU 0 (
        echo Python 3 is required but was not found on PATH.
        exit /b 1
    )
    set "PYTHON=python"
)

if not exist "%VENV_DIR%\Scripts\python.exe" (
    %PYTHON% -m venv "%VENV_DIR%"
    if not %ERRORLEVEL% EQU 0 exit /b %ERRORLEVEL%
)

"%VENV_DIR%\Scripts\python.exe" -m pip install --upgrade pip
if not %ERRORLEVEL% EQU 0 exit /b %ERRORLEVEL%

"%VENV_DIR%\Scripts\python.exe" -m pip install -r "%SCRIPT_DIR%requirements.txt"
if not %ERRORLEVEL% EQU 0 exit /b %ERRORLEVEL%

echo Local environment is ready.
echo Start the app with: start-app.bat start
