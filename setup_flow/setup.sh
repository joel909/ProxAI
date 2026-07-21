#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
VENV_DIR="${PROJECT_DIR}/.venv"

if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: Python 3 is required but was not found." >&2
    echo "Install Python 3 and its venv package using your Linux distribution's package manager." >&2
    exit 1
fi

if ! python3 -c 'import sys; raise SystemExit(sys.version_info < (3, 10))'; then
    echo "Error: ProxAI requires Python 3.10 or newer." >&2
    exit 1
fi

if [[ ! -x "${VENV_DIR}/bin/python" ]]; then
    echo "Creating virtual environment at ${VENV_DIR}"
    if ! python3 -m venv "${VENV_DIR}"; then
        echo "Error: Python's venv module is unavailable." >&2
        echo "Install the python3-venv package, then run this script again." >&2
        exit 1
    fi
fi

"${VENV_DIR}/bin/python" -m pip install --upgrade pip
"${VENV_DIR}/bin/python" -m pip install -r "${PROJECT_DIR}/requirements.txt"

echo
echo "Generating device manifest..."
"${VENV_DIR}/bin/python" "${SCRIPT_DIR}/generate_manifest.py"

echo
echo "Setup complete. Start ProxAI with:"
echo "  ${SCRIPT_DIR}/run.sh"
