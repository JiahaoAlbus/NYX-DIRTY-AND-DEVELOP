# Q9 Exchange Spec v1 (Testnet Alpha)

## Purpose
Define the Testnet Alpha exchange module scope, boundaries, and deterministic evidence obligations for Q9.

## Scope
- Testnet Alpha exchange actions with deterministic evidence outputs.
- Order placement, cancellation, orderbook listing, and trade listing.
- Evidence export per action using the immutable Evidence Format v1.

## Non-Scope
- No live market data or external price feeds.
- No account or identity semantics.
- No real payment rails or custody guarantees.

## Definitions
- **Order**: A deterministic intent to buy or sell a testnet instrument pair.
- **Trade**: A deterministic match record created by the matching engine.
- **Evidence Bundle**: The immutable evidence fields and artifacts produced per action.

## Normative Rules (MUST / MUST NOT)
- An exchange action MUST be labeled as Testnet Alpha in UI and documentation.
- An exchange action MUST produce a deterministic evidence bundle with fields:
  protocol_anchor, inputs, outputs, receipt_hashes, state_hash, replay_ok, stdout.
- The backend MUST validate all order inputs using bounded integer ranges.
- The backend MUST reject oversized payloads and invalid fields with deterministic errors.
- The exchange module MUST NOT use external price feeds or real market data.
- The exchange module MUST NOT add account, login, or identity semantics.
- The exchange module MUST NOT claim live trading or real asset settlement.

## Evidence and Replay
- Evidence artifacts MUST be deterministic for identical inputs.
- Evidence export MUST be byte-for-byte stable for the same inputs.
- The replay_ok field MUST reflect successful deterministic replay of the evidence bundle.

## Security Boundaries
- Order placement and cancellation MUST be rate limited.
- Evidence export MUST use allowlisted artifact names and safe path resolution.

## Evidence / Verification Mapping
- Unit tests for matching and fee invariants.
- Determinism test for exchange evidence artifacts.
- Smoke test for exchange endpoints and orderbook listing.

## Freeze / Change Control
- This specification is normative for Q9 Testnet Alpha.
- Any change requires an explicit version bump and new evidence mapping.
