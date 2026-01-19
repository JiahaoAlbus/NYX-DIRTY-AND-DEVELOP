# Q6 Evidence Ledger Template

Purpose
- Provide a stable template for recording execution evidence.

Scope
- Q6 weekly evidence entries and release window proof.

Non-Scope
- Storage of secrets or sensitive material.

MUST and MUST NOT
- Evidence entries MUST include command, output summary, and hash references.
- Evidence entries MUST NOT contain secrets or witness data.
- Each entry MUST include timestamp in UTC and operator identifier.

Template
- Week:
- Date (UTC):
- Operator:
- Command:
- Output summary:
- PROPERTY_N:
- Hashes:
- Notes:

Evidence / Verification
- Commands are in `docs/AUDIT_REPRO_COMMANDS.md`.

Freeze / Change Control
- Template is execution-only; no protocol semantics.
