#!/usr/bin/env bash
set -euo pipefail

echo "[conformance] NYX frozen-rules gate running..."

###############################################################################
# Forbidden implementation patterns
# NOTE:
# - These patterns are meant to catch *implementations*, not documentation.
# - Do NOT include allowlist/whitelist here while scanning docs is disabled.
###############################################################################
FORBIDDEN_PATTERNS='
wallet[[:space:]]*=[[:space:]]*identity
wallet.*identity
identity.*wallet
admin.*bypass
privileged.*bypass
fee.*exempt
support override
'

###############################################################################
# Scan scope
# - DO NOT scan documentation directories (规则 / 规划 / docs)
# - DO NOT scan shell scripts (including this file itself)
# - Focus only on implementation-adjacent areas
###############################################################################
TARGET_DIRS=".github packages tooling"

for d in $TARGET_DIRS; do
  if [ ! -d "$d" ]; then
    continue
  fi

  echo "[conformance] scanning $d"

  echo "$FORBIDDEN_PATTERNS" | while IFS= read -r re; do
    [ -z "$re" ] && continue

    if grep -RIn \
        --exclude-dir=.git \
        --exclude-dir=node_modules \
        --exclude="*.sh" \
        -E "$re" "$d" >/dev/null 2>&1; then

      echo "[conformance] FAIL: forbidden pattern detected"
      echo "pattern: $re"
      echo "location:"
      grep -RIn \
        --exclude-dir=.git \
        --exclude-dir=node_modules \
        --exclude="*.sh" \
        -E "$re" "$d" || true

      exit 1
    fi
  done
done

echo "[conformance] OK"
