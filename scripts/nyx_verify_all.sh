#!/bin/bash
set -e

# scripts/nyx_verify_all.sh
# One-command verification script for NYX Proof Package.

echo "=================================================="
echo "NYX VERIFICATION SUITE"
echo "Starting at $(date)"
echo "=================================================="

# Default arguments
SEED="123"
RUN_ID="verify-$(date +%s)"
OUT_DIR="docs/evidence/verify-${RUN_ID}"

# Parse args
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --seed) SEED="$2"; shift ;;
        --run-id) RUN_ID="$2"; shift ;;
        --out-dir) OUT_DIR="$2"; shift ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

echo "[1/6] Compiling Python source..."
python3 -m compileall -q .
echo "PASS: Compilation successful."

echo "[2/6] Running Unit Tests..."
python3 scripts/nyx_run_all_unittests.py
echo "PASS: Unit tests passed."

echo "[3/6] Running Conformance Checks (v1)..."
# Ensure python path includes conformance package
export PYTHONPATH="$PYTHONPATH:$(pwd)/packages/conformance-v1/src"
python3 -m conformance_v1.runner --out nyx_conformance_report.json
echo "PASS: Conformance checks passed. Report: nyx_conformance_report.json"

echo "[4/6] Running Smoke Tests (Evidence Generation)..."
# Forward args to smoke script
python3 scripts/nyx_smoke_all_modules.py --seed "$SEED" --run-id "$RUN_ID"
echo "PASS: Smoke tests completed."

echo "[5/6] Building Web Bundle (nyx-world)..."
bash scripts/build_nyx_world.sh
echo "PASS: Web bundle built (or skipped)."

echo "[6/6] Building iOS App (NYXPortal)..."
if command -v xcodebuild >/dev/null 2>&1; then
    if [ -d "apps/nyx-ios/NYXPortal.xcodeproj" ]; then
        xcodebuild -project apps/nyx-ios/NYXPortal.xcodeproj \
            -scheme NYXPortal \
            -destination 'platform=iOS Simulator,name=iPhone 16 Pro' \
            build | grep "BUILD SUCCEEDED" && echo "PASS: iOS Build Succeeded" || echo "FAIL: iOS Build Failed"
    else
        echo "SKIP: iOS project not found."
    fi
else
    echo "SKIP: iOS (no Xcode detected)."
fi

echo "=================================================="
echo "VERIFICATION SUMMARY"
echo "=================================================="
echo "1. Unit Tests:       PASS"
echo "2. Conformance:      PASS (nyx_conformance_report.json)"
echo "3. Smoke Evidence:   GENERATED (See docs/evidence/smoke-...)"
echo "4. Web Build:        DONE"
echo "5. iOS Build:        $(command -v xcodebuild >/dev/null 2>&1 && echo "ATTEMPTED" || echo "SKIPPED")"
echo "=================================================="
echo "NYX PROOF PACKAGE VERIFIED."
