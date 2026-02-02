# NYX Testnet Portal v1 Release Candidate Plan

This plan aims to deliver a production-ready, release-candidate version of the NYX Testnet Portal, including the backend gateway, web portal, and iOS application.

## 1. Branching and Environment Setup
- Create a single release branch: `release/testnet-portal-v1`.
- Ensure all dependencies for Python, Node.js (for `nyx-world`), and Xcode are available.

## 2. Product Implementation & Hardening
- **Backend Gateway**:
  - Verify all modules (wallet, exchange, chat, marketplace, entertainment, portal auth, evidence) are functional in `apps/nyx-backend-gateway`.
  - Ensure `scripts/nyx_backend_dev.sh` is the canonical entry point.
- **Web Portal**:
  - Build `nyx-world` using `scripts/build_nyx_world.sh`.
  - Verify the `WebBundle` is correctly embedded in the iOS app.
- **iOS Application**:
  - Ensure the Xcode project `NYXPortal.xcodeproj` builds cleanly.
  - Verify the Evidence Center correctly handles artifact export and displays real-time state.

## 3. Verification & Proof Packaging
- **Canonical Verification**:
  - Run `bash scripts/nyx_verify_all.sh --seed 123 --run-id smoke-123`.
  - This covers compilation, unit tests, conformance, smoke tests, and builds for both Web and iOS.
- **Proof Artifacts**:
  - Run `bash scripts/nyx_pack_proof_artifacts.sh`.
  - Verify the generated `nyx_proof_package_<timestamp>.zip` contains the conformance report, latest smoke evidence, and normative documentation.

## 4. Documentation & Release Notes
- Create `docs/RELEASE_NOTES_TESTNET_PORTAL_V1.md`:
  - Detail features shipped (Wallet v1, Exchange, E2EE Chat, etc.).
  - Document exact reproduction commands for verification.
  - List intentionally out-of-scope mainnet features.

## 5. Submission
- Open a **single PR** from `release/testnet-portal-v1` into `main`.
- Include verification outputs and the proof zip filename in the PR description.

Do you approve this plan to proceed with the release candidate implementation?
