#!/usr/bin/env bash

# Fail on error and catch errors in pipes. 
# (-u is intentionally omitted to prevent crashing the Python activate script)
set -eo pipefail

# Change to the directory where the script is located
cd "$(dirname "$0")" || exit

if [ -d ".venv" ]; then
    # Activate the virtual environment
    source .venv/bin/activate
else
    echo "[WARNING] No .venv folder found in this directory."
    echo "Running with the default system Python environment..."
    echo ""
fi

# Run the Python script
python3 beetle_core/embeetle.py -n -d