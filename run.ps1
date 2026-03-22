Set-Location $PSScriptRoot

if (Test-Path ".venv") {
    .venv\Scripts\Activate.ps1
} else {
    Write-Host "[WARNING] No .venv folder found in this directory."
    Write-Host "Running with the default system Python environment..."
    Write-Host ""
}

python beetle_core\embeetle.py -n -d
