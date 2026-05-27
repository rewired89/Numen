# Numen startup script for Windows PowerShell
# Usage:
#   .\numen.ps1              - start on port 7860
#   .\numen.ps1 --port 8080  - start on custom port
#   .\numen.ps1 --share      - generate public Gradio link

param(
    [int]$Port = 7860,
    [switch]$Share
)

Write-Host ""
Write-Host "  _   _                           " -ForegroundColor Cyan
Write-Host " | \ | |_   _ _ __ ___   ___ _ __" -ForegroundColor Cyan
Write-Host " |  \| | | | | '_ `` _ \ / _ \ '_ \" -ForegroundColor Cyan
Write-Host " | |\  | |_| | | | | | |  __/ | | |" -ForegroundColor Cyan
Write-Host " |_| \_|\__,_|_| |_| |_|\___|_| |_|" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Math Solver for Everyone  v1.0.0" -ForegroundColor White
Write-Host "  ──────────────────────────────────" -ForegroundColor DarkGray

# Create venv if it doesn't exist
if (-not (Test-Path "venv")) {
    Write-Host ""
    Write-Host "  [setup] First run — creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  [error] Could not create venv. Is Python installed?" -ForegroundColor Red
        Write-Host "  Download Python from https://python.org" -ForegroundColor Red
        exit 1
    }

    Write-Host "  [setup] Installing Numen..." -ForegroundColor Yellow
    & venv\Scripts\pip install -e . --quiet
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  [error] Installation failed. See output above." -ForegroundColor Red
        exit 1
    }
    Write-Host "  [setup] Done!" -ForegroundColor Green
}

Write-Host ""
Write-Host "  Starting at http://localhost:$Port" -ForegroundColor Green
Write-Host "  Press Ctrl+C to stop." -ForegroundColor DarkGray
Write-Host ""

if ($Share) {
    & venv\Scripts\numen up --port $Port --share
} else {
    & venv\Scripts\numen up --port $Port
}
