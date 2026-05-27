@echo off
:: Numen startup script for Windows
:: Double-click this file or run it from PowerShell/CMD

title Numen - Math Solver

echo.
echo   _   _
echo  ^| \ ^| ^|_   _ _ __ ___   ___ _ __
echo  ^|  \^| ^| ^| ^| ^| '_ ` _ \ / _ \ '_ \
echo  ^| ^|\  ^| ^|_^| ^| ^| ^| ^| ^| ^|  __/ ^| ^| ^|
echo  ^|_^| \_^|\__,_^|_^| ^|_^| ^|_^|\___^|_^| ^|_^|
echo.
echo  Math Solver for Everyone  v1.0.0
echo  ─────────────────────────────────────

:: Check if venv exists, create it if not
if not exist "venv\" (
    echo  [setup] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo  [error] Failed to create venv. Is Python installed?
        echo  Download Python from https://python.org
        pause
        exit /b 1
    )
    echo  [setup] Installing Numen dependencies...
    venv\Scripts\pip install -e . --quiet
    if errorlevel 1 (
        echo  [error] pip install failed. See above for details.
        pause
        exit /b 1
    )
    echo  [setup] Done!
    echo.
)

:: Parse optional port argument  (numen.bat --port 8080)
set PORT=7860
:parse_args
if "%~1"=="--port" (
    set PORT=%~2
    shift
    shift
    goto parse_args
)
if "%~1"=="-p" (
    set PORT=%~2
    shift
    shift
    goto parse_args
)

echo  Starting Numen at http://localhost:%PORT%
echo  Press Ctrl+C to stop.
echo.

venv\Scripts\numen up --port %PORT%

pause
