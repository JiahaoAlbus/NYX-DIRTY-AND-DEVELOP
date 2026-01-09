# L2 Economics - Fee Engine v0

This package defines the NYX L2 Economics fee engine with strict shared-state mutation rules, sponsor equivalence, and auditable fee vectors.

## Shared-State Mutation

- `ActionKind.READ_ONLY`: read-only actions may quote a zero fee.
- `ActionKind.STATE_MUTATION`: shared-state mutations must quote a non-zero fee.
- The action kind is defined by `ActionDescriptor.kind` and cannot be overridden by callers.

## Fee Vector Components

Fee vectors are stable, ordered tuples of components:
- `BASE` (must be > 0 for state mutations)
- `BYTES` (size-dependent)
- `COMPUTE` (placeholder for compute accounting)

**Structural non-zero rule**: for `STATE_MUTATION`, the fee total is always > 0 and `BASE` is always > 0.

## Sponsor Semantics

`sponsor()` only changes the payer. The fee vector and action hash remain identical before/after sponsorship.

## Auditability

- `ActionDescriptor.canonical_bytes()` produces a stable JSON encoding.
- `action_hash`, `quote_hash`, and `receipt_hash` are reproducible offline.
- `FeeVector.canonical_bytes()` and `sha256()` allow component-by-component verification.

## No Privileged Paths

This engine contains no allowlist, bypass, or debug free lane mechanisms.
