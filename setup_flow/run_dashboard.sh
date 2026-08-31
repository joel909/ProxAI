#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
UVICORN="${PROJECT_DIR}/.venv/bin/uvicorn"

if [[ ! -x "${UVICORN}" ]]; then
    echo "Dashboard dependencies are missing. Run ${SCRIPT_DIR}/setup.sh first." >&2
    exit 1
fi

cd "${PROJECT_DIR}"
exec "${UVICORN}" dashboard.app:app \
    --host "${PROXAI_DASHBOARD_HOST:-127.0.0.1}" \
    --port "${PROXAI_DASHBOARD_PORT:-7681}"
