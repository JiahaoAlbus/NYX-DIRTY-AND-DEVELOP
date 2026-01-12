# Invariants & Gates (Testnet 0.1)

## Core Invariants (frozen)
- Identity ≠ wallet ≠ chain account; chain sender/signature never equals identity.
- State mutation actions must incur non-zero fee; sponsor may change payer only, never amount.
- Proof context separation: any proof verified under the wrong context must fail.
- Wallet-kernel is verify-only; it cannot generate proofs or handle root secrets.
- Chain signatures are not identity, and no module imports sealed identity roots.

## Gate Stack
- Frozen Q1 Lock (frozen docs + manifest integrity)
- Law Guard / Frozen Rules Gate (conformance-v1)
- SAST + Dependency Scan (pipeline defaults)
- CI unittest discovery pinned to `packages/l0-identity/test/**/*_test.py`

## Security Boundary
NYX Testnet 0.1 uses mock/stdlib implementations only; nothing here constitutes production-grade cryptography or key management.
