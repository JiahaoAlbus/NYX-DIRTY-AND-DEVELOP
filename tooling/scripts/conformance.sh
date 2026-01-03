#!/usr/bin/env bash
set -e

echo "[conformance] NYX frozen-rules gate running..."

# Forbidden patterns (simple grep-based gate)
FORBIDDEN_PATTERNS="
wallet[[:space:]]*=[[:space:]]*identity
wallet.*identity
identity.*wallet
admin.*bypass
privileged.*bypass
fee.*exempt
allowlist
whitelist
support override
"

TARGET_DIRS="tooling 规则 .github"

for d in $TARGET_DIRS; do
  if [ -d "$d" ]; then
    echo "[conformance] scanning $d"
    echo "$FORBIDDEN_PATTERNS" | while read -r re; do
      if [ -n "$re" ]; then
        if grep -RIn --exclude-dir=.git -E "$re" "$d" >/dev/null 2>&1; then
          echo "[conformance] FAIL: forbidden pattern detected: $re in $d"
          grep -RIn --exclude-dir=.git -E "$re" "$d" || true
          exit 1
        fi
      fi
    done
  fi
done

echo "[conformance] OK"
