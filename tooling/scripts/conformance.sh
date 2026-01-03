#!/usr/bin/env bash
set -euo pipefail

echo "[conformance] NYX frozen-rules gate running..."

# Heuristic guardrails: block obvious forbidden patterns.
# Starter gate now; evolve into executable spec tests in Q2.
FORBIDDEN_REGEX=(
  "wallet[[:space:]]*=[[:space:]]*identity"
  "wallet.*identity"
  "identity.*wallet"
  "admin.*bypass"
  "privileged.*bypass"
  "fee.*exempt"
  "allowlist"
  "whitelist"
  "support override"
)

TARGET_DIRS=("packages" "tooling" "docs" "规则" "specs" ".github")

for d in "${TARGET_DIRS[@]}"; do
  if [ -d "$d" ]; then
    for re in "${FORBIDDEN_REGEX[@]}"; do
      if grep -RIn --exclude-dir=.git --exclude-dir=node_modules -E "$re" "$d" >/dev/null 2>&1; then
        echo "[conformance] FAIL: forbidden pattern detected: $re in $d"
        grep -RIn --exclude-dir=.git --exclude-dir=node_modules -E "$re" "$d" || true
        exit 1
      fi
    done
  fi
done

echo "[conformance] OK"
