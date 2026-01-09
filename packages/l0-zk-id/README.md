# L0 ZK-ID (Week 3 Extreme)

This package implements the Week 3 ZK-ID proof envelope, strict context separation, and a stateless mock prover/adapter for auditability.

## Core Design

- **ProofEnvelope** binds `protocol_version`, `statement_id`, `context_id`, `nonce`, and canonical `public_inputs` to a `binding_tag`.
- **Law layer** (`verify_envelope`) is ZK-system agnostic and always enforced.
- **Adapter layer** (`verify_proof`) is replaceable; the mock adapter can be swapped with a real ZK verifier later without touching the envelope or law layer.

## Proof Envelope (Law Layer)

Fields:
- `protocol_version` (string)
- `statement_id` (string)
- `context_id` (bytes32)
- `nonce` (bytes32)
- `public_inputs` (dict)
- `proof_bytes` (bytes)
- `binding_tag` (bytes32)
- `nullifier` (optional bytes32)

**Binding tag formula**:
```
binding_tag = SHA256(
  DOMAIN ||
  len(protocol_version) || protocol_version ||
  len(statement_id) || statement_id ||
  context_id(32) ||
  nonce(32) ||
  Canonical(public_inputs)
)
```
`DOMAIN = "NYX:ZKID:PROOF_ENVELOPE:v1"`

**Canonicalization** (public inputs and witness hashing):
- Supported types: `dict(str->value)`, `list/tuple`, `str`, `int` (non-bool), `bool`, `None`.
- Rejected types: `float/NaN/Inf`, `bytes/bytearray`, `set`, custom objects.
- JSON output uses `sort_keys=True`, `separators=(",", ":")`, `ensure_ascii=False`, UTF-8 encoding.
- Surrogate code points are rejected to keep UTF-8 semantics stable.

## Mock Prover / Adapter (Stateless)

Mock-only field:
- `_mock_witness_hash` is injected into `public_inputs` during proving (hex string). It is **mock-only** and must not be used in real ZK adapters.

Mock proof formula:
```
witness_hash = SHA256(Canonical(witness))
proof_bytes = SHA256("NYX:MOCK_PROOF:v1" || binding_tag || witness_hash)
```
Verification reads `_mock_witness_hash` from `public_inputs` and recomputes `proof_bytes` without any adapter state.

## Context Separation (Structural)

Context separation is enforced by construction:
- `context_id` is part of `binding_tag` and must match the expected context.
- `verify_envelope` recomputes `binding_tag` and rejects any mismatch.
- Changing context (even with identical proofs) **always fails**.

## Nullifier (Optional, Frozen Formula)

```
nullifier = SHA256(
  "NYX:ZKID:NULLIFIER:v1" ||
  context_id ||
  statement_id ||
  epoch_or_nonce ||
  secret_commitment
)
```

## Notes

- This package does **not** modify or depend on `packages/l0-identity/`.
- Only the adapter layer is expected to change when swapping in a real ZK system.
