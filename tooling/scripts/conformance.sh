#!/usr/bin/env bash
set -euo pipefail

echo "[conformance] NYX frozen-rules gate running..."

# Simple grep-based gate (starter). Evolve into executable conformance tests in Q2.
FORBIDDEN_PATTERNS='
wallet[[:space:]]*=[[:space:]]*identity
wallet.*identity
identity.*wallet
admin.*bypass
privileged.*bypass
fee.*exempt
allowlist
whitelist
support override
'

# Keep scope small for now to avoid false positives/noise.
TARGET_DIRS="tooling 规则 .github"

for d in $TARGET_DIRS; do
  if [ -d "$d" ]; then
    echo "[conformance] scanning $d"
    echo "$FORBIDDEN_PATTERNS" | while IFS= read -r re; do
      [ -z "$re" ] && continue
      if grep -RIn --exclude-dir=.git --exclude-dir=node_modules -E "$re" "$d" >/dev/null 2>&1; then
        echo "[conformance] FAIL: forbidden pattern detected: $re in $d"
        grep -RIn --exclude-dir=.git --exclude-dir=node_modules -E "$re" "$d" || true
        exit 1
      fi
    done
  fi
done

echo "[conformance] OK"
