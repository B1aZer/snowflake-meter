#!/usr/bin/env bash
#   ./run.sh meter.py --pattern spread --n 40
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p results
source .venv/bin/activate
exec python "$@"
