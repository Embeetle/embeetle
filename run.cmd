@echo off
cd /d "%~dp0"

if exist ".venv\" (
    call .venv\Scripts\activate.bat
) else (
    echo [WARNING] No .venv folder found in this directory.
    echo Running with the default system Python environment...
    echo.
)

python beetle_core\embeetle.py -n -d