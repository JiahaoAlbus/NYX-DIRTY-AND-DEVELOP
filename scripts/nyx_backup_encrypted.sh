#!/usr/bin/env bash
set -euo pipefail

# Encrypted backup for NYX gateway data + evidence.
# Requires: openssl (AES-256-GCM + PBKDF2)

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TS="$(date +%Y%m%d_%H%M%S)"
OUT_DIR="${NYX_BACKUP_OUT_DIR:-$ROOT/release_artifacts/backups}"
PASSPHRASE="${NYX_BACKUP_PASSPHRASE:-}"
PBKDF2_ITER="${NYX_BACKUP_PBKDF2_ITER:-1000000}"
PBKDF2_DIGEST="${NYX_BACKUP_PBKDF2_DIGEST:-sha512}"
KEY_FILE="${NYX_BACKUP_KEY_FILE:-}"

if [[ -z "$PASSPHRASE" && -n "$KEY_FILE" && -f "$KEY_FILE" ]]; then
  PASSPHRASE="$(cat "$KEY_FILE")"
fi

if [[ -z "$PASSPHRASE" ]]; then
  echo "❌ Set NYX_BACKUP_PASSPHRASE or NYX_BACKUP_KEY_FILE for encryption."
  exit 1
fi

DB_PATH="${NYX_GATEWAY_DB_PATH:-$ROOT/apps/nyx-backend-gateway/data/nyx_gateway.db}"
RUNS_DIR="$ROOT/apps/nyx-backend-gateway/runs"
EVIDENCE_DIR="$ROOT/docs/evidence"

EXTRA_PATHS="${NYX_BACKUP_PATHS:-}"

mkdir -p "$OUT_DIR"

TMP_TAR="$(mktemp /tmp/nyx_backup_XXXXXX.tar.gz)"
MANIFEST="$OUT_DIR/nyx-backup-${TS}.manifest.json"
OUT_FILE="$OUT_DIR/nyx-backup-${TS}.tar.gz.enc"

echo "🧩 Packing data..."
tar -czf "$TMP_TAR" \
  "$DB_PATH" \
  "$RUNS_DIR" \
  "$EVIDENCE_DIR" \
  ${EXTRA_PATHS}

SHA256="$(sha256sum "$TMP_TAR" | awk '{print $1}')"

echo "🔐 Encrypting..."
openssl enc -aes-256-gcm -salt -pbkdf2 -iter "$PBKDF2_ITER" -md "$PBKDF2_DIGEST" \
  -pass env:NYX_BACKUP_PASSPHRASE \
  -in "$TMP_TAR" -out "$OUT_FILE"

cat > "$MANIFEST" <<EOF
{
  "timestamp": "$TS",
  "backup_file": "$(basename "$OUT_FILE")",
  "sha256": "$SHA256",
  "pbkdf2_iter": "$PBKDF2_ITER",
  "pbkdf2_digest": "$PBKDF2_DIGEST",
  "db_path": "$DB_PATH",
  "runs_dir": "$RUNS_DIR",
  "evidence_dir": "$EVIDENCE_DIR",
  "extra_paths": "${EXTRA_PATHS}"
}
EOF

rm -f "$TMP_TAR"

echo "✅ Encrypted backup ready: $OUT_FILE"
echo "✅ Manifest: $MANIFEST"
