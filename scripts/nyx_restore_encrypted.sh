#!/usr/bin/env bash
set -euo pipefail

# Restore encrypted NYX backup created by nyx_backup_encrypted.sh
# Requires: openssl

if [[ $# -lt 1 ]]; then
  echo "Usage: bash scripts/nyx_restore_encrypted.sh <backup-file.tar.gz.enc> [restore_dir]"
  exit 1
fi

BACKUP_FILE="$1"
RESTORE_DIR="${2:-./nyx_restore}"

PASSPHRASE="${NYX_BACKUP_PASSPHRASE:-}"
KEY_FILE="${NYX_BACKUP_KEY_FILE:-}"

if [[ -z "$PASSPHRASE" && -n "$KEY_FILE" && -f "$KEY_FILE" ]]; then
  PASSPHRASE="$(cat "$KEY_FILE")"
fi

if [[ -z "$PASSPHRASE" ]]; then
  echo "❌ Set NYX_BACKUP_PASSPHRASE or NYX_BACKUP_KEY_FILE for decryption."
  exit 1
fi

mkdir -p "$RESTORE_DIR"

TMP_TAR="$(mktemp /tmp/nyx_restore_XXXXXX.tar.gz)"

echo "🔓 Decrypting..."
openssl enc -d -aes-256-gcm -pbkdf2 -iter 600000 \
  -pass env:NYX_BACKUP_PASSPHRASE \
  -in "$BACKUP_FILE" -out "$TMP_TAR"

echo "📦 Restoring to $RESTORE_DIR..."
tar -xzf "$TMP_TAR" -C "$RESTORE_DIR"
rm -f "$TMP_TAR"

echo "✅ Restore complete: $RESTORE_DIR"
