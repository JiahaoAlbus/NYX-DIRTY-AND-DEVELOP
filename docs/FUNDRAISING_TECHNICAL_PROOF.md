# Fundraising Technical Proof (Testnet Only)

## Purpose
Provide a deterministic, reproducible validation workflow for the NYX Testnet platform and the evidence export guarantees.

## Scope
- Backend gateway modules: wallet, exchange, chat, marketplace, entertainment, portal auth.
- Deterministic evidence and export bundles.
- Testnet only (no mainnet claims).

## Non-Scope
- Mainnet settlement.
- KYC or identity binding.
- External wallets or price feeds.

## Verification (One Command)
Run:
- `scripts/nyx_fundraising_validate.sh`

Expected outputs:
- `docs/evidence/fundraising/latest/` contains evidence and export artifacts.
- `docs/evidence/fundraising/latest/logs/` contains logs for smoke, compile, unit tests, and conformance.
- `apps/nyx-ios/WebBundle/` is refreshed from the nyx-world build.
- iOS build logs are captured when `xcodebuild` is available.

## Evidence Artifacts
- Evidence bundles are written by the backend, exported verbatim, and must include:
  - `protocol_anchor`
  - `inputs`
  - `outputs`
  - `receipt_hashes`
  - `state_hash`
  - `replay_ok`
  - `stdout`

## UI Wiring Evidence
- The web UI is bundled into the iOS app and reads backend base URL from runtime injection.
- Native Evidence Center lists runs and exports `export.zip` without modifying evidence fields.

## Security and Integrity
- Deterministic outputs for the same seed/run_id and payloads.
- Protocol fee remains non-zero on value-moving actions.
- Platform fee is additive and never replaces protocol fee.

## Known Limits (Facts)
- Testnet only. No mainnet connectivity.
- No external wallet connect or identity binding.
