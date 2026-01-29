#!/bin/bash
set -e

# scripts/nyx_pack_proof_artifacts.sh
# Collects verified artifacts into a redistributable ZIP.

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
EXPORT_DIR="docs/evidence/${TIMESTAMP}_proof_package"
ZIP_NAME="nyx_proof_package_${TIMESTAMP}.zip"

echo "Packing proof artifacts into $EXPORT_DIR..."

mkdir -p "$EXPORT_DIR"

# 1. Conformance Report
if [ -f "nyx_conformance_report.json" ]; then
    cp nyx_conformance_report.json "$EXPORT_DIR/"
else
    echo "WARN: nyx_conformance_report.json not found. Run verify script first."
fi

# 2. Latest Smoke Evidence
# Find the most recent smoke directory
LATEST_SMOKE=$(ls -td docs/evidence/smoke/*/ | head -1)
if [ -n "$LATEST_SMOKE" ]; then
    echo "Including latest smoke evidence: $LATEST_SMOKE"
    cp -r "$LATEST_SMOKE" "$EXPORT_DIR/smoke_evidence"
else
    echo "WARN: No smoke evidence found."
fi

# 3. Documentation (The Proof Package itself)
mkdir -p "$EXPORT_DIR/docs"
cp -r docs/proof "$EXPORT_DIR/docs/"
cp -r docs/funding "$EXPORT_DIR/docs/"

# 4. Create ZIP
echo "Zipping..."
# Use -X to exclude extended attributes for better deterministic behavior on macOS
zip -r -X "$ZIP_NAME" "$EXPORT_DIR"

echo "=================================================="
echo "PROOF PACKAGE CREATED: $ZIP_NAME"
echo "=================================================="
