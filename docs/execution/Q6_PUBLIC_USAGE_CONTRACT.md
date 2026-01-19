# Q6 Public Usage Contract

Purpose
- Define the deterministic usage contract for public execution and verification.

Scope
- Commands, outputs, and evidence required for public reproducibility.

Non-Scope
- Any protocol change or semantic change.

MUST and MUST NOT
- Public usage MUST use the canonical verification commands.
- Outputs MUST be deterministic for identical inputs.
- The contract MUST NOT include secrets or sensitive material.

Usage Contract
- Canonical verification command:
  - `python -m compileall packages/l0-identity/src`
  - `python -m unittest discover -s packages/l0-identity/test -p "*_test.py" -v`
- Determinism requirement: identical inputs MUST produce identical summaries.

Evidence / Verification
- See `docs/AUDIT_REPRO_COMMANDS.md` for the canonical command list.

Freeze / Change Control
- Execution-only contract; no protocol changes.
