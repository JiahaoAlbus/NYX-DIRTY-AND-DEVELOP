# NYX Testnet 0.1

NYX is an identity-first protocol with sealed Week1–Week8 foundations. Testnet 0.1 ships the first end-to-end path from identity proof to fee enforcement and chain receipt.

## Quick Start (Testnet 0.1)
```bash
git checkout testnet-0.1
python -m compileall packages/l0-identity/src
python -m unittest discover -s packages/l0-identity/test -p "*_test.py" -v
PYTHONPATH="packages/l0-identity/src:packages/l2-economics/src:packages/l1-chain/src:packages/wallet-kernel/src:packages/l0-zk-id/src:packages/e2e-demo/src" \
python -m e2e_demo.run_demo --out /tmp/nyx_w7_trace.json --seed 123
```
Runbook with details: `docs/TESTNET_0_1_RUNBOOK.md`.

## What You Must Not Change
- Sealed foundations (identity, zk-id, fee engine, l1 chain, wallet-kernel, e2e-demo) are break-glass only.
- See `docs/SEALING_AND_BREAK_GLASS.md` for the full list and process.

## Security Boundary
Mock/stdlib implementations only; no production-grade cryptography or HSM/keystore. Invariants and gate summary: `docs/INVARIANTS_AND_GATES.md`.
