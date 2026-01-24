# Q10 Architecture V1

## Purpose
Specify the Q10 Testnet Beta architecture for iOS, backend gateway, and evidence export.

## Scope
iOS app shell, backend gateway, storage, evidence export, and fee routing.

## Non-Scope
No protocol semantic changes; no mainnet operations.

## Architecture Overview
- iOS app: unified world entry with module navigation and evidence viewer.
- Backend gateway: module APIs, strict validation, deterministic evidence export.
- Storage: deterministic records for orders, messages, listings, and receipts.
- Fee routing: protocol fee enforced, platform fee additive, treasury routing by env.

## Normative Requirements (MUST / MUST NOT)
- All module actions that move value MUST enforce protocol fee > 0.
- Platform fee MUST be additive and MUST NOT replace protocol fee.
- Evidence export MUST be deterministic and replayable.
- Backend MUST validate inputs, enforce size caps, and prevent path traversal.
- iOS app MUST NOT claim live mainnet status or show external price feeds.

## Evidence / Verification
- python -m compileall packages/l0-identity/src
- python scripts/nyx_run_all_unittests.py
- PYTHONPATH="packages/conformance-v1/src" python -m conformance_v1.runner --out nyx_conformance_report.json

## Freeze / Change Control
- Architecture changes require additive extensions only and regression evidence.
