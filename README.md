# NYX Testnet
Deterministic, verifiable portal infrastructure.

## Proof Run (~15min)
Verify the entire project state (tests, conformance, smoke runs, builds) with one command:
```bash
bash scripts/nyx_verify_all.sh
```

## Demo (~10min)
See the guided demo script: [docs/proof/DEMO_SCRIPT.md](docs/proof/DEMO_SCRIPT.md).

## Documentation
- **Technical Overview**: [docs/proof/NYX_TECHNICAL_OVERVIEW.md](docs/proof/NYX_TECHNICAL_OVERVIEW.md)
- **Reproducibility**: [docs/proof/REPRODUCIBILITY.md](docs/proof/REPRODUCIBILITY.md)
- **Funding & Grants**: [docs/funding/README.md](docs/funding/README.md)

## Quick Start (Dev)
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

## Public Usage Contract (Q6)
Deterministic verification commands and output contract: `docs/execution/Q6_PUBLIC_USAGE_CONTRACT.md`.
