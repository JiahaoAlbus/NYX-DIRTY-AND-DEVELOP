#!/bin/bash
set -e

# NYX Proof Artifacts Packaging Script
# Collects all required documentation and verification logs into a single bundle.

BUNDLE_NAME="nyx-testnet-proof-v1.tar.gz"
ARTIFACTS_DIR="release_artifacts"

echo "📦 Packaging NYX Proof Artifacts..."

# 1. Run verification if logs missing
if [ ! -d "$ARTIFACTS_DIR/verify_logs" ]; then
    echo "⚠️ Verification logs missing. Running verify script..."
    bash scripts/nyx_verify_all.sh
fi

# 2. Collect Docs
cp docs/ENDPOINT_INVENTORY.md "$ARTIFACTS_DIR/"
cp docs/UI_ACTION_INVENTORY.md "$ARTIFACTS_DIR/"
cp docs/FUNCTIONALITY_MATRIX_TESTNET_V1.md "$ARTIFACTS_DIR/"
cp docs/MAINNET_PARITY.md "$ARTIFACTS_DIR/"

# 3. Create Bundle
tar -czf "$BUNDLE_NAME" -C "$ARTIFACTS_DIR" .

echo "✅ Proof bundle created: $BUNDLE_NAME"
echo "Contents:"
tar -tf "$BUNDLE_NAME"
