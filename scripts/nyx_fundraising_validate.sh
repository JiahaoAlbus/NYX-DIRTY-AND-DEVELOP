#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_ROOT="$ROOT/docs/evidence/fundraising/latest/logs"
OUT_DIR="$ROOT/docs/evidence/fundraising/latest"
PYTHON_BIN="${PYTHON:-python}"

mkdir -p "$LOG_ROOT"

backend_log="$LOG_ROOT/backend.log"
smoke_log="$LOG_ROOT/smoke.log"
compile_log="$LOG_ROOT/compile.log"
unittest_log="$LOG_ROOT/unittests.log"
conformance_log="$LOG_ROOT/conformance.log"
build_web_log="$LOG_ROOT/build_web.log"
build_ios_log="$LOG_ROOT/build_ios.log"
gate_ios_log="$LOG_ROOT/gate_ios.log"
gate_web_log="$LOG_ROOT/gate_web.log"

NYX_FORCE_RESTART=1 "$ROOT/scripts/nyx_backend_dev.sh" >"$backend_log" 2>&1 &
BACKEND_PID=$!

ready=0
for _ in $(seq 1 50); do
  if command -v curl >/dev/null 2>&1; then
    if curl -fsS "http://127.0.0.1:8091/healthz" | tr -d ' ' | grep -q '"ok":true'; then
      ready=1
      break
    fi
  else
    "$PYTHON_BIN" - <<'PY'
import sys
import urllib.request

try:
    with urllib.request.urlopen("http://127.0.0.1:8091/healthz", timeout=0.5) as resp:
        body = resp.read().decode("utf-8", errors="ignore")
    if '"ok":true' in body.replace(" ", ""):
        sys.exit(0)
except Exception:
    pass
sys.exit(1)
PY
    if [ $? -eq 0 ]; then
      ready=1
      break
    fi
  fi
  sleep 0.2
done

if [ "$ready" -ne 1 ]; then
  echo "Backend not ready on http://127.0.0.1:8091" >&2
  if ps -p "$BACKEND_PID" >/dev/null 2>&1; then
    kill "$BACKEND_PID" >/dev/null 2>&1 || true
  fi
  exit 1
fi

"$PYTHON_BIN" "$ROOT/scripts/nyx_smoke_all_modules.py" \
  --seed 123 \
  --run-id smoke-123 \
  --base-url http://127.0.0.1:8091 \
  --out-dir "$OUT_DIR" >"$smoke_log" 2>&1

"$ROOT/scripts/build_nyx_world.sh" >"$build_web_log" 2>&1

"$PYTHON_BIN" -m compileall "$ROOT/packages/l0-identity/src" >"$compile_log" 2>&1
"$PYTHON_BIN" "$ROOT/scripts/nyx_run_all_unittests.py" >"$unittest_log" 2>&1
PYTHONPATH="$ROOT/packages/conformance-v1/src" "$PYTHON_BIN" -m conformance_v1.runner --out "$ROOT/nyx_conformance_report.json" >"$conformance_log" 2>&1

if command -v xcodebuild >/dev/null 2>&1; then
  xcodebuild -project "$ROOT/apps/nyx-ios/NYXPortal.xcodeproj" -scheme NYXPortal -destination 'platform=iOS Simulator,name=iPhone 16 Pro' build >"$build_ios_log" 2>&1
else
  echo "WARN: xcodebuild not available; skipping iOS build" >"$build_ios_log"
fi

"$PYTHON_BIN" "$ROOT/scripts/nyx_ios_no_fake_gate.py" >"$gate_ios_log" 2>&1
"$PYTHON_BIN" "$ROOT/scripts/no_fake_gate_web.py" >"$gate_web_log" 2>&1

if ps -p "$BACKEND_PID" >/dev/null 2>&1; then
  kill "$BACKEND_PID" >/dev/null 2>&1 || true
fi

printf "OK: evidence at %s\n" "$OUT_DIR"
printf "OK: logs at %s\n" "$LOG_ROOT"
