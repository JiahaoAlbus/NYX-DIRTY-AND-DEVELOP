# NYX Backend Gateway (Testnet Alpha)

Purpose
- Provide a storage layer and gateway surface for Q9 testnet flows.

Scope
- Storage primitives for orders, trades, messages, listings, purchases, receipts, and evidence runs.
- Deterministic, schema-based persistence for testnet alpha.
- Gateway API for deterministic evidence runs and artifact export.

Non-Scope
- No protocol semantics changes.
- No identity or account semantics.
- No production guarantees.

Endpoints
- POST /run (seed, run_id, module, action, payload)
- POST /exchange/place_order (seed, run_id, payload: side/asset_in/asset_out/amount/price)
- POST /exchange/cancel_order (seed, run_id, payload: order_id)
- POST /chat/send (seed, run_id, payload: channel/message)
- GET /status?run_id=...
- GET /evidence?run_id=...
- GET /artifact?run_id=...&name=...
- GET /export.zip?run_id=...
- GET /list
- GET /exchange/orders
- GET /exchange/orderbook
- GET /exchange/trades
- GET /chat/messages?channel=...

Run (local)
- python -m nyx_backend_gateway.server --env-file .env.example

Verification
- Storage migrations and roundtrip tests under `apps/nyx-backend-gateway/test`.

Change Control
- Additive only; no changes to sealed protocol behavior.
