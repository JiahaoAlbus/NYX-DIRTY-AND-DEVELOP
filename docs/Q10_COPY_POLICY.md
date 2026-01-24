# Q10 Copy Policy

## Purpose
Define mandatory copy rules for Testnet Beta UI and documentation to avoid misleading claims.

## Scope
Applies to all UI copy, docs, and API responses introduced or updated in Q10.

## Non-Scope
Does not change protocol semantics or evidence fields.

## Normative Rules (MUST / MUST NOT)
- UI copy MUST state "Testnet Beta" for all product surfaces.
- UI copy MUST NOT claim live operational status, uptime, or network health.
- UI copy MUST NOT claim real market data, external price feeds, or live trading.
- UI copy MUST NOT include login, signup, or external wallet connect claims.
- Evidence fields MUST be displayed verbatim and MUST NOT be paraphrased.

## Allowed Phrases (Examples)
- "Testnet Beta"
- "Provided by backend"
- "Not live data"
- "Evidence is deterministic and replayable"

## Disallowed Phrases (Examples)
- "Mainnet live"
- "Synced"
- "Consensus active"
- "Real-time prices"
- "Wallet connected"

## Evidence / Verification
- Conformance drills MUST fail if disallowed phrases are introduced.
