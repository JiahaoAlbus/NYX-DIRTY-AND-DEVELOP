# Wallet Kernel SDK (Week 6)

Wallet kernel provides chain-level key management, transaction plumbing, and proof carriage with verify-only checks.
It does not treat sender data as user identity.

## Scope
- Chain signing keys and HMAC-based placeholder signatures
- Transaction build/sign/submit using `l1-chain` types
- Proof carriage and verify-only checks using `l0-zk-id`
- Policy contracts for multisig, spend limits, and social recovery (interfaces only)

## Invariants
- No root-secret intake, storage, serialization, or API surface
- Chain sender and signatures are chain-level only
- Proof plumbing verifies existing envelopes only; it does not generate proofs
- Core objects are frozen with strict validation

## Usage
This module is designed to be imported by higher-level components in Week 7/8 without modifying sealed packages.
