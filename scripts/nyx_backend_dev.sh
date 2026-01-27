#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON:-python}"
VENV_DIR="$ROOT/.venv"

if [ ! -d "$VENV_DIR" ]; then
  set +e
  "$PYTHON_BIN" -m venv "$VENV_DIR"
  VENV_STATUS=$?
  set -e
  if [ $VENV_STATUS -ne 0 ]; then
    echo "WARN: venv creation failed; continuing with system python"
    VENV_DIR=""
  fi
fi

if [ -n "$VENV_DIR" ] && [ -f "$VENV_DIR/bin/activate" ]; then
  # shellcheck disable=SC1091
  source "$VENV_DIR/bin/activate"
  PYTHON_BIN="$VENV_DIR/bin/python"
fi

export PYTHONPATH="$ROOT/apps/nyx-backend-gateway/src:$ROOT/apps/nyx-backend/src"

ENV_FILE="$ROOT/.env.example"
if [ -f "$ROOT/cswdz.env" ]; then
  ENV_FILE="$ROOT/cswdz.env"
fi

check_health() {
  "$PYTHON_BIN" - <<'PY'
import sys
import urllib.request

url = "http://127.0.0.1:8091/healthz"
try:
    with urllib.request.urlopen(url, timeout=0.5) as resp:
        body = resp.read().decode("utf-8", errors="ignore")
    if '"ok":true' in body.replace(" ", ""):
        sys.exit(0)
except Exception:
    pass
sys.exit(1)
PY
}

FORCE_RESTART="${NYX_FORCE_RESTART:-0}"
if check_health; then
  if [ "$FORCE_RESTART" != "1" ]; then
    echo "READY http://127.0.0.1:8091 (already running)"
    exit 0
  fi
  echo "Healthy backend detected; restarting due to NYX_FORCE_RESTART=1"
fi

LISTENER_PID=""
if command -v lsof >/dev/null 2>&1; then
  LISTENER_PID="$(lsof -tiTCP:8091 -sTCP:LISTEN || true)"
fi

if [ -n "$LISTENER_PID" ]; then
  echo "Port 8091 in use without healthy backend; stopping PID $LISTENER_PID"
  kill "$LISTENER_PID" >/dev/null 2>&1 || true
  sleep 1
fi

"$PYTHON_BIN" -m nyx_backend_gateway.server --host 127.0.0.1 --port 8091 --env-file "$ENV_FILE" &
SERVER_PID=$!

"$PYTHON_BIN" - <<'PY'
import socket
import sys
import time

host = "127.0.0.1"
port = 8091

deadline = time.time() + 10
while time.time() < deadline:
    sock = socket.socket()
    try:
        sock.settimeout(0.2)
        sock.connect((host, port))
        sock.close()
        sys.exit(0)
    except OSError:
        time.sleep(0.2)

sys.exit(1)
PY

if [ $? -ne 0 ]; then
  echo "Backend failed to bind to 127.0.0.1:8091" >&2
  kill "$SERVER_PID" >/dev/null 2>&1 || true
  exit 1
fi

echo "READY http://127.0.0.1:8091"
wait "$SERVER_PID"
