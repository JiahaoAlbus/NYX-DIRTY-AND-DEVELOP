# Q10 Exchange Spec (Testnet Beta)

## Purpose
Define the testnet exchange flow and its constraints for Q10.

## Scope
- Order placement and cancellation.
- Orderbook queries and trade history.
- Evidence and fee routing expectations.

## Non-Scope
- External price feeds or live market data.
- Mainnet claims or real-world settlement.
- User identity or account profiles.

## Normative Rules (MUST / MUST NOT)
1) Exchange actions MUST be deterministic for the same seed and payload.
2) Exchange actions MUST generate evidence bundles that include required fields:
   protocol_anchor, inputs, outputs, receipt_hashes, state_hash, replay_ok, stdout.
3) Order payloads MUST validate numeric bounds for amount and price.
4) Exchange actions MUST route protocol fees and MUST NOT allow fee bypass.
5) Exchange UI MUST NOT show external market data or real-world pricing.
6) Exchange UI MUST label testnet behavior explicitly.

## Evidence / Verification
- Unit tests validate order placement, cancellation, and deterministic evidence outputs.
- Conformance runner verifies fee and evidence invariants.

## Freeze / Change Control
This spec is normative for Q10 Testnet Beta. Changes require a versioned update and regression evidence.
