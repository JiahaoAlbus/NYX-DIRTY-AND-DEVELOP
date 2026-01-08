# L0 Identity Skeleton

Purpose
- Define the non-account-based identity boundary for L0.
- Establish local-only root secret generation and context-bound derivation.

Boundaries
- This package is the only Week 2 implementation entry point.
- No business logic, protocol, or gateway code belongs here.
- Dependencies are limited to the standard library.

Prohibited inputs
- address
- account
- wallet
- pubkey
- globalId

Root Secret
- Generated locally only; no import from external identifiers.
- Export/serialization is prohibited; only redacted output is permitted.

Context
- Required for every derivation and serialization.
- Domain separation is enforced with a fixed tag.

Serialization
- Requires explicit Context input.
- Output is context-bound and non-stable across time.

State machine
- Created -> Active -> Rotated -> Destroyed
- Destroyed is terminal; derive/serialize/use is forbidden.

API boundary
- Creation and use accept only RootSecret and Context types.
- Runtime guard rejects account-like identifiers (0x..., did:pkh, eip155) with code NYX_CONFORMANCE_WALLET_AS_IDENTITY.

Tests
- Placeholder tests exist and will be replaced with L0 coverage in PR2.
