#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
PYTHON="${PROJECT_DIR}/.venv/bin/python"

if [[ ! -x "${PYTHON}" ]]; then
    echo "The project environment has not been set up yet." >&2
    echo "Run ${SCRIPT_DIR}/setup.sh first." >&2
    exit 1
fi

cd "${PROJECT_DIR}"
exec "${PYTHON}" "${PROJECT_DIR}/main.py" "$@"

