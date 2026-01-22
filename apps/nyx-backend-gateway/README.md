# NYX Backend Gateway (Testnet Alpha)

Purpose
- Provide a storage layer and gateway surface for Q9 testnet flows.

Scope
- Storage primitives for orders, trades, messages, listings, purchases, receipts, and evidence runs.
- Deterministic, schema-based persistence for testnet alpha.

Non-Scope
- No protocol semantics changes.
- No identity or account semantics.
- No production guarantees.

Verification
- Storage migrations and roundtrip tests under `apps/nyx-backend-gateway/test`.

Change Control
- Additive only; no changes to sealed protocol behavior.
