# NYX First App (Example)

This is an upper-layer example. It consumes sealed modules and does not modify protocol behavior.

## What it does
- Runs a state mutation with a non-zero fee
- Binds a commitment in the action payload
- Produces a receipt and replayable trace

## How to run
```bash
PYTHONPATH="apps/nyx-first-app/src:packages/e2e-demo/src:packages/wallet-kernel/src:packages/l1-chain/src:packages/l2-economics/src:packages/l0-zk-id/src" \
python -m nyx_first_app.cli --seed 123 --out /tmp/nyx_app_trace.json
```

Expected summary fields include:
`fee_total`, `tx_hash`, `block_hash`, `state_root`, `receipt_hash`, `replay_ok=True`.

## Boundaries
- Example only; not production cryptography
- No root secret output or persistence
- Uses Testnet 0.1 components as-is
