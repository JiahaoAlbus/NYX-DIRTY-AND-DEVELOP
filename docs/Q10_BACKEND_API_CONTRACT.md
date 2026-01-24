# Q10 Backend API Contract (Testnet Beta)

## Purpose
Define the stable backend gateway API surface for Q10 Testnet Beta.

## Scope
- HTTP endpoints for exchange, chat, marketplace, entertainment, and wallet.
- Request/response fields and validation rules.
- Evidence export endpoints.

## Non-Scope
- Any mainnet claims.
- External wallet integrations.
- UI behavior or styling.

## Normative Rules (MUST / MUST NOT)
1) All requests MUST include an explicit `seed` and `run_id` for evidence-producing actions.
2) `run_id` MUST match `[A-Za-z0-9_-]{1,64}` and MUST NOT contain path separators.
3) Evidence endpoints MUST return the evidence fields verbatim:
   - protocol_anchor, inputs, outputs, receipt_hashes, state_hash, replay_ok, stdout
4) Export bundles MUST be deterministic (stable ordering, fixed timestamps, no environment metadata).
5) Payloads MUST be validated for bounds and types; invalid payloads MUST return 400.
6) The API MUST NOT expose identity, login, or external wallet semantics.
7) All economic actions MUST be routed through protocol fee enforcement.

## Endpoints (Testnet Beta)
### Evidence
- POST /run
- GET /status?run_id=...
- GET /evidence?run_id=...
- GET /artifact?run_id=...&name=...
- GET /export.zip?run_id=...
- GET /list

### Exchange
- POST /exchange/place_order
- POST /exchange/cancel_order
- GET /exchange/orders
- GET /exchange/orderbook
- GET /exchange/trades

### Chat
- POST /chat/send
- GET /chat/messages?channel=...

### Marketplace
- POST /marketplace/listing
- POST /marketplace/purchase
- GET /marketplace/listings
- GET /marketplace/purchases?listing_id=...

### Entertainment
- POST /entertainment/step
- GET /entertainment/items
- GET /entertainment/events?item_id=...

### Wallet
- POST /wallet/faucet
- POST /wallet/transfer
- GET /wallet/balance?address=...

## Evidence / Verification
- Canonical tests: `python scripts/nyx_run_all_unittests.py`
- Conformance runner: `PYTHONPATH="packages/conformance-v1/src" python -m conformance_v1.runner --out nyx_conformance_report.json`

## Freeze / Change Control
This contract is normative for Q10 Testnet Beta. Changes require a versioned update and regression evidence.
