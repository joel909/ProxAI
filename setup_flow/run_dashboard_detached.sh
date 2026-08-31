#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${PROXAI_DASHBOARD_LOG:-/tmp/proxai-dashboard.log}"
PID_FILE="${PROXAI_DASHBOARD_PID_FILE:-/tmp/proxai-dashboard.pid}"

if [[ -f "${PID_FILE}" ]]; then
    EXISTING_PID="$(<"${PID_FILE}")"
    if kill -0 "${EXISTING_PID}" 2>/dev/null; then
        echo "Dashboard is already running with PID ${EXISTING_PID}."
        exit 0
    fi
fi

export PROXAI_DASHBOARD_HOST="${PROXAI_DASHBOARD_HOST:-0.0.0.0}"

nohup "${SCRIPT_DIR}/run_dashboard.sh" </dev/null >>"${LOG_FILE}" 2>&1 &
DASHBOARD_PID=$!
echo "${DASHBOARD_PID}" >"${PID_FILE}"

sleep 1
if ! kill -0 "${DASHBOARD_PID}" 2>/dev/null; then
    echo "Dashboard failed to start. Check ${LOG_FILE}." >&2
    exit 1
fi

echo "Dashboard started with PID ${DASHBOARD_PID}. Logs: ${LOG_FILE}"
