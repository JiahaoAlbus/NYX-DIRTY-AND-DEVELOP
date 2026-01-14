# E2E Private Transfer (Week5)

This package provides a deterministic end-to-end demo for a private ledger action.

## Scope
- Private ledger action proof wiring and verification
- Fee quote and enforce via L2 economics
- Chain execution on devnet with receipt and replay
- Deterministic trace for offline verification

## Notes
- Secret material stays in memory only
- tx assembly via wallet-kernel (proofs carried only)
- identity commitment is derived locally and stored as hex

## Running
See run_demo.py for the CLI entrypoint.
