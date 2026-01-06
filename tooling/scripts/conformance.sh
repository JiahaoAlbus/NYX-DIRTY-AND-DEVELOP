#!/usr/bin/env bash
set -euo pipefail

echo "[conformance] NYX frozen-rules gate running..."

###############################################################################
# Forbidden implementation patterns
# NOTE:
# - These patterns are meant to catch implementations, not documentation.
# - Do NOT include allowlist/whitelist here while scanning docs is disabled.
###############################################################################
RULES_FILE="${CONFORMANCE_RULES_FILE:-conformance/rules/patterns.txt}"

LEGACY_RULES='
Q1-001|critical|wallet[[:space:]]*=[[:space:]]*identity|Wallet is not identity
Q1-001|critical|wallet.*identity|Wallet is not identity
Q1-001|critical|identity.*wallet|Wallet is not identity
Q1-004|critical|admin.*bypass|No trusted administrators
Q1-004|critical|privileged.*bypass|No trusted administrators
Q1-002|critical|fee.*exempt|No privileged fee exemptions
Q1-004|critical|support override|No trusted administrators
'

if [ -f "$RULES_FILE" ]; then
  RULES_CONTENT=$(cat "$RULES_FILE")
else
  echo "[conformance] WARN: rules file not found at $RULES_FILE, using legacy patterns"
  RULES_CONTENT="$LEGACY_RULES"
fi

###############################################################################
# Scan scope
# - DO NOT scan documentation directories (rules/plans/docs)
# - DO NOT scan shell scripts (including this file itself)
# - Focus only on implementation-adjacent areas
###############################################################################
TARGET_DIRS=".github packages tooling"

for d in $TARGET_DIRS; do
  if [ ! -d "$d" ]; then
    continue
  fi

  echo "[conformance] scanning $d"

  while IFS= read -r line; do
    [ -z "$line" ] && continue
    case "$line" in
      \#*) continue ;;
    esac

    IFS='|' read -r rule_id severity pattern summary <<< "$line"
    [ -z "$pattern" ] && continue

    matches=$(grep -RIn \
        --exclude-dir=.git \
        --exclude-dir=node_modules \
        --exclude="*.sh" \
        -E "$pattern" "$d" || true)

    if [ -n "$matches" ]; then
      first=$(printf '%s\n' "$matches" | head -n 1)
      echo "[conformance] FAIL: rule $rule_id"
      echo "severity: $severity"
      echo "summary: $summary"
      echo "pattern: $pattern"
      echo "match: $first"
      echo "CONFORMANCE_FAIL|$rule_id|$severity|$summary|$first"
      exit 1
    fi
  done <<< "$RULES_CONTENT"
done

echo "[conformance] OK"