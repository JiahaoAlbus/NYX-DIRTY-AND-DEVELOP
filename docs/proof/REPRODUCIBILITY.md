# Reproducibility Guide

## Purpose
This document defines the prerequisites and steps to reproduce the NYX project artifacts from source. The goal is to allow any third party to verify the build integrity with a single command.

## Prerequisites

### System Requirements
-   **OS**: macOS (recommended for iOS build) or Linux (Ubuntu 22.04+).
-   **Python**: 3.10+ (managed via `pyenv` recommended).
-   **Node.js**: 18+ (for WebBundle build).
-   **Xcode**: 15+ (optional, for iOS build; required for full verification).

### Dependencies
-   Python packages: Listed in `requirements.txt` (or installed via modules).
-   Node modules: `npm install` in `nyx-world`.

## One-Command Verification

To run the full verification pipeline:

```bash
bash scripts/nyx_verify_all.sh
```

### What This Script Does
1.  **Compilation**: `python -m compileall` to ensure no syntax errors.
2.  **Unit Tests**: Runs all Python unit tests across modules.
3.  **Conformance**: Runs the Conformance Runner (v1) to verify protocol rules.
4.  **Smoke Tests**: Runs end-to-end smoke tests against a local backend instance, generating evidence.
5.  **Web Build**: Builds the `nyx-world` React app.
6.  **iOS Build**: Builds the `NYXPortal` iOS app (skips if Xcode is missing).

## Expected Artifacts

After a successful run, you will find:

1.  **Conformance Report**: `nyx_conformance_report.json` (Root).
2.  **Smoke Evidence**: `docs/evidence/<timestamp>/` containing JSON evidence bundles and ZIP exports.
3.  **Web Bundle**: `apps/nyx-world/dist/` (or similar build output).
4.  **iOS App**: `apps/nyx-ios/build/` (if on macOS with Xcode).

## Manual Verification Steps

### 1. Python Environment
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt # (if present, or install modules individually)
```

### 2. Conformance
```bash
PYTHONPATH="packages/conformance-v1/src" python -m conformance_v1.runner --out nyx_conformance_report.json
```

### 3. Smoke Test
```bash
python scripts/nyx_smoke_all_modules.py --run-id manual-verify-1
```

## Troubleshooting

-   **Missing Xcode**: The script will print "SKIP iOS (no Xcode)" and continue. This is expected on Linux CI.
-   **Port Conflicts**: Ensure ports 8000-8090 are free for the smoke test backend launcher.
-   **Python Path**: Ensure `PYTHONPATH` is set correctly if running individual scripts (the automation scripts handle this).
