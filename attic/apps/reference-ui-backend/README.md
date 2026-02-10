# NYX Reference UI Backend (Week 5)

## Purpose
Provide a deterministic backend wrapper around the evidence generator.

## Scope
- Evidence generation and export.
- Static asset serving for the reference UI.

## Non-Scope
- Protocol semantics.
- Live system data.
- Any authentication or account handling.

## Run (Dev)
```
PYTHONPATH="apps/reference-ui-backend/src:packages/e2e-private-transfer/src:packages/l2-private-ledger/src:packages/l0-zk-id/src:packages/l2-economics/src:packages/l1-chain/src:packages/wallet-kernel/src" \
  python -m nyx_reference_ui_backend.server
```

## API
- POST /run
- GET /status?run_id=...
- GET /evidence?run_id=...
- GET /artifact?run_id=...&name=...
- GET /export.zip?run_id=...
- GET /list
