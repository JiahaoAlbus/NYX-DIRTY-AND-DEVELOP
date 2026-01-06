#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
cd "$ROOT_DIR"

FROZEN_DIR="frozen/q1"
MANIFEST="${CONFORMANCE_MANIFEST_FILE:-conformance/frozen-manifest.sha256}"
BREAK_GLASS_DOC="docs/break-glass.md"

if [ ! -d "$FROZEN_DIR" ]; then
  echo "[conformance] WARN: $FROZEN_DIR not found; skipping frozen verification"
  exit 0
fi

if [ ! -f "$MANIFEST" ]; then
  echo "[conformance] FAIL: frozen manifest missing: $MANIFEST"
  echo "[conformance] See $BREAK_GLASS_DOC for break-glass procedure."
  exit 1
fi

echo "[conformance] verifying frozen manifest hashes..."
if ! sha256sum -c "$MANIFEST"; then
  echo "[conformance] FAIL: frozen manifest hash mismatch"
  echo "[conformance] See $BREAK_GLASS_DOC for break-glass procedure."
  exit 1
fi

manifest_entries=$(sed -E 's/^[0-9a-f]{64}  //' "$MANIFEST")
missing=0
while IFS= read -r -d '' file; do
  rel="${file#./}"
  if ! printf '%s\n' "$manifest_entries" | grep -Fxq "$rel"; then
    echo "[conformance] FAIL: missing manifest entry: $rel"
    missing=1
  fi
done < <(find "$FROZEN_DIR" -type f -print0)

if [ "$missing" -ne 0 ]; then
  echo "[conformance] See $BREAK_GLASS_DOC for break-glass procedure."
  exit 1
fi

extra=0
while IFS= read -r entry; do
  [ -z "$entry" ] && continue
  if [ ! -f "$entry" ]; then
    echo "[conformance] FAIL: manifest entry missing on disk: $entry"
    extra=1
  fi
done <<< "$manifest_entries"

if [ "$extra" -ne 0 ]; then
  echo "[conformance] See $BREAK_GLASS_DOC for break-glass procedure."
  exit 1
fi

dupe=0
while IFS= read -r entry; do
  [ -z "$entry" ] && continue
  base=$(basename "$entry")
  if [ "$base" = "README.md" ]; then
    continue
  fi
  matches=$(find . -type f -name "$base" ! -path "./$FROZEN_DIR/*" ! -path "./.git/*")
  if [ -n "$matches" ]; then
    echo "[conformance] FAIL: duplicate authoritative candidate for $base"
    echo "$matches"
    dupe=1
  fi
done <<< "$manifest_entries"

if [ "$dupe" -ne 0 ]; then
  echo "[conformance] See $BREAK_GLASS_DOC for break-glass procedure."
  exit 1
fi

echo "[conformance] frozen integrity OK"