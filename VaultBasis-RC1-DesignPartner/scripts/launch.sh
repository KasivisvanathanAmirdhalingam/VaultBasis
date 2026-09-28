#!/usr/bin/env bash
set -eo pipefail

# ==============================================================================
# VaultBasis — Industrial Local Edge & Web Application Launcher
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

HOST="127.0.0.1"
PORT="8000"

echo "================================================================================"
echo "          VAULTBASIS EDGE — INDUSTRIAL LOCAL LAUNCHER                           "
echo "================================================================================"
echo "Initializing VaultBasis local trust boundary..."

# Ensure data directory exists
mkdir -p data/keys

# Check if port is already in use
if lsof -Pi :${PORT} -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️ Port ${PORT} is already in use. Checking existing process..."
    EXISTING_PID=$(lsof -Pi :${PORT} -sTCP:LISTEN -t)
    echo "Killing conflicting process on port ${PORT} (PID ${EXISTING_PID})..."
    kill -9 "${EXISTING_PID}" 2>/dev/null || true
    sleep 1
fi

echo "Starting Edge REST API and Web Application on http://${HOST}:${PORT}..."
export PYTHONPATH="${REPO_ROOT}"

# Start uvicorn with auto-reload
uvicorn edge.api.app:app --host "${HOST}" --port "${PORT}" --reload --log-level info &
SERVER_PID=$!

# Trap signals for graceful shutdown
cleanup() {
    echo ""
    echo "Shutting down VaultBasis Edge service (PID ${SERVER_PID})..."
    kill -15 "${SERVER_PID}" 2>/dev/null || true
    wait "${SERVER_PID}" 2>/dev/null || true
    echo "VaultBasis Edge stopped cleanly."
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# Healthcheck loop (wait up to 10 seconds)
echo "Waiting for Edge service to reach HEALTHY state..."
MAX_RETRIES=20
RETRY_COUNT=0
HEALTH_OK=0

while [ ${RETRY_COUNT} -lt ${MAX_RETRIES} ]; do
    if curl -s "http://${HOST}:${PORT}/api/health" | grep -q '"status":"HEALTHY"'; then
        HEALTH_OK=1
        break
    fi
    sleep 0.5
    RETRY_COUNT=$((RETRY_COUNT + 1))
done

if [ ${HEALTH_OK} -eq 1 ]; then
    echo "--------------------------------------------------------------------------------"
    echo "✅ VAULTBASIS EDGE IS LIVE AND FULLY OPERATIONAL!"
    echo "--------------------------------------------------------------------------------"
    echo "📍 Web Dashboard (Customer UI):   http://${HOST}:${PORT}/"
    echo "📍 Preview Marketing Page:        http://${HOST}:${PORT}/about"
    echo "📍 Public Offline Verifier Tool:   http://${HOST}:${PORT}/verifier"
    echo "📍 Local REST API Documentation:   http://${HOST}:${PORT}/docs"
    echo "📍 Health & Diagnostic Endpoint:   http://${HOST}:${PORT}/api/health"
    echo "--------------------------------------------------------------------------------"
    echo "Press Ctrl+C to stop the local service."
    echo "================================================================================"
    
    # Wait for the server process
    wait "${SERVER_PID}"
else
    echo "❌ ERROR: Healthcheck timed out after 10 seconds. Check server logs."
    exit 1
fi
