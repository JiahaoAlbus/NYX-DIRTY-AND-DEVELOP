#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON:-python}"
VENV_DIR="$ROOT/.venv"

if [ "${NYX_DEV_NO_VENV:-}" != "1" ]; then
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
  if [ -n "${VENV_DIR:-}" ] && [ -f "$VENV_DIR/bin/activate" ]; then
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"
    PYTHON_BIN="$VENV_DIR/bin/python"
  fi
fi

export PYTHONPATH="$ROOT/apps/nyx-backend-gateway/src:$ROOT/apps/nyx-backend/src"

ENV_FILE="$ROOT/.env.example"
if [ -f "$ROOT/cswdz.env" ]; then
  ENV_FILE="$ROOT/cswdz.env"
fi

HOST="${NYX_DEV_HOST:-127.0.0.1}"
PORT="${NYX_DEV_PORT:-8091}"

check_health() {
  "$PYTHON_BIN" - <<PY
import sys
import urllib.request

url = f"http://{HOST}:{PORT}/healthz"
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
    echo "READY http://${HOST}:${PORT} (already running)"
    exit 0
  fi
  echo "Healthy backend detected; restarting due to NYX_FORCE_RESTART=1"
fi

LISTENER_PID=""
if command -v lsof >/dev/null 2>&1; then
  LISTENER_PID="$(lsof -tiTCP:${PORT} -sTCP:LISTEN || true)"
fi

if [ -n "$LISTENER_PID" ]; then
  echo "Port ${PORT} in use without healthy backend; stopping PID $LISTENER_PID"
  kill "$LISTENER_PID" >/dev/null 2>&1 || true
  sleep 1
fi

"$PYTHON_BIN" -m nyx_backend_gateway.server --host "$HOST" --port "$PORT" --env-file "$ENV_FILE" &
SERVER_PID=$!

"$PYTHON_BIN" - <<PY
import socket
import sys
import time
import urllib.request

host = "${HOST}"
port = int("${PORT}")

def check_health():
    try:
        with urllib.request.urlopen(f"http://{host}:{port}/healthz", timeout=0.5) as resp:
            body = resp.read().decode("utf-8", errors="ignore")
        return '\"ok\":true' in body.replace(" ", "")
    except Exception:
        return False

deadline = time.time() + 10
while time.time() < deadline:
    sock = socket.socket()
    try:
        sock.settimeout(0.2)
        sock.connect((host, port))
        sock.close()
        if check_health():
            sys.exit(0)
    except OSError:
        time.sleep(0.2)
    time.sleep(0.2)

sys.exit(1)
PY

if [ $? -ne 0 ]; then
  echo "Backend failed to become healthy on ${HOST}:${PORT}" >&2
  kill "$SERVER_PID" >/dev/null 2>&1 || true
  exit 1
fi

echo "READY http://${HOST}:${PORT}"
wait "$SERVER_PID"
