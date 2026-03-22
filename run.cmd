@echo off
cd /d "%~dp0"

if defined PSModulePath (
    echo [ERROR] This script must be run from a CMD terminal, not PowerShell.
    echo         Open a CMD terminal and run: run.cmd
    exit /b 1
)

if exist ".venv\" (
    call .venv\Scripts\activate.bat
) else (
    echo [WARNING] No .venv folder found in this directory.
    echo Running with the default system Python environment...
    echo.
)

python beetle_core\embeetle.py -n -d