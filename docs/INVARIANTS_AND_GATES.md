# Invariants & Gates (Testnet 0.1)

## Core Invariants (frozen)
- Identity is separate from chain account and sender.
- Chain sender/signature never equals identity.
- State mutation actions must incur non-zero fee; sponsor may change payer only, never amount.
- Client kernel is verify-only; it cannot generate proofs or handle root secrets.
- Chain signatures carry no identity meaning, and no module imports sealed identity roots.

## Gate Stack
- Frozen Q1 Lock (frozen docs + manifest integrity)
- Law Guard / Frozen Rules Gate (conformance-v1)
- SAST + Dependency Scan (pipeline defaults)
- CI unittest discovery pinned to `packages/l0-identity/test/**/*_test.py`

## Security Boundary
NYX Testnet 0.1 uses mock/stdlib implementations only; nothing here constitutes production-grade cryptography or key management.
