# Reference Client v1 Spec

Purpose
- Define the deterministic reference client behavior for Router v1.

Scope
- CLI execution, deterministic report format, and replay verification.

Non-Scope
- End-user UI, key handling, secret storage, or any identity semantics.
- Production cryptography or external integrations.

MUST and MUST NOT
- The client MUST execute Router actions deterministically with a fixed seed.
- The client MUST output a report with stable ordering and no secrets.
- The client MUST print: state_hash, receipt_chain, replay_ok.
- The client MUST include a deterministic step panel showing reserves, LP, output, and fee_charged.
- The client MUST use integer-only values; floats are forbidden.
- The client MUST NOT derive meaning from sender or signer fields.
- The client MUST NOT generate or store secrets, witness data, or root material.

Evidence / Verification
- `attic/apps/nyx-reference-client/test/client_smoke_test.py`
- `attic/apps/nyx-reference-client/test/determinism_guard_test.py`

Freeze / Change Control
- Client output format is frozen after Week07 (F1).
- After F1: only patch changes with no semantic drift and regression proof.
