#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_DIR="$ROOT/nyx-world"
OUT_DIR="$ROOT/apps/nyx-ios/WebBundle"

if [ ! -f "$APP_DIR/package.json" ]; then
  echo "nyx-world package.json not found" >&2
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "npm is required to build nyx-world" >&2
  exit 1
fi

cd "$APP_DIR"

if [ -f package-lock.json ]; then
  npm ci --no-audit --no-fund
else
  npm install --no-audit --no-fund
fi

npm run build

rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR"

cp -R "$APP_DIR/dist/." "$OUT_DIR/"

echo "OK: WebBundle written to $OUT_DIR"
