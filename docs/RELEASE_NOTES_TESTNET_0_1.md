# Release Notes — NYX Testnet 0.1

## Contents (Week3–Week8 highlights)
- Week3: ZK-ID mock envelope with binding tag + context separation.
- Week4: L2 Fee Engine v0 (no free actions, sponsor only swaps payer).
- Week5: L1 chain adapter + deterministic devnet (chain signatures ≠ identity).
- Week6: Wallet-kernel SDK (verify-only, no root-secret handling).
- Week7: End-to-end pipeline (identity -> fee -> chain -> receipt) with replayable trace.
- Week8: Conformance v1 red-team drills (Frozen Rules Gate).

## Known Limitations
- Mock cryptography only; no production-grade proving, signing, or HSM/keystore.
- Devnet is deterministic and single-node; not a distributed chain.

## Command Index
- Runbook: `docs/TESTNET_0_1_RUNBOOK.md`
- Audit Checklist: `docs/AUDIT_CHECKLIST_TESTNET_0_1.md`
- Sealing & Break-Glass: `docs/SEALING_AND_BREAK_GLASS.md`
