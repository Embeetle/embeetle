#!/usr/bin/env bash
set -euo pipefail
# activate the venv
source "$(dirname "$0")/../venv/bin/activate"
# run the IDE from beetle_core
cd "$(dirname "$0")/beetle_core"
python embeetle.py -n -d
