# RELEASE NOTES: NYX Testnet Portal v1 (Release Candidate)

## Overview
This release candidate ships the first production-grade, user-usable version of the NYX Testnet Portal. It integrates the core Five-Layer architecture into a unified user experience across Web and iOS, backed by a deterministic gateway service.

## What's Shipped
### A. Backend Gateway
- **Unified API**: A robust Python-based gateway mediating all module interactions.
- **Modules Enabled**:
  - **Wallet**: Faucet and transfer with protocol fee enforcement.
  - **Exchange**: Limit order book, order placement, and cancellation.
  - **Chat**: End-to-end encrypted messaging rooms.
  - **Marketplace**: Listing publication and peer-to-peer purchasing.
  - **Entertainment**: Deterministic state steps for interactive modules.
  - **Portal Auth**: Secure challenge-response authentication.
  - **Evidence**: Real-time evidence generation and artifact export.

### B. Web Portal (nyx-world)
- **Modern UI**: React-based dashboard for all testnet modules.
- **Deterministic state**: Renders real state from the gateway (no placeholders).
- **Embedded WebBundle**: Pre-built and ready for iOS integration.

### C. iOS Application (NYXPortal)
- **Native Experience**: SwiftUI app with embedded Web portal.
- **Evidence Center**: Native interface to view and export cryptographic proof of actions.
- **Configurable**: Settings to point to local or remote gateway endpoints.

## Reproducibility & Verification
The entire project state can be verified with a single command:
```bash
bash scripts/nyx_verify_all.sh --seed 123 --run-id smoke-123
```
This runs:
1. Python compilation
2. 580+ unit tests
3. Conformance checks against Q1 frozen specs
4. Smoke tests for all modules
5. Web portal build
6. iOS application build

### Packaging Proof
To generate a redistributable proof package:
```bash
bash scripts/nyx_pack_proof_artifacts.sh
```
Produces: `nyx_proof_package_<timestamp>.zip`

## Out of Scope (Intentionally)
- **Mainnet features**: No live mainnet data or token value.
- **Production Cryptography**: Uses protocol-native primitives (no HSM integration).
- **Public Hosting**: Designed for local/devnet usage in this RC.

## Verification Artifacts
- **Conformance Report**: `nyx_conformance_report.json`
- **Latest Proof Zip**: `nyx_proof_package_20260202_133152.zip`
