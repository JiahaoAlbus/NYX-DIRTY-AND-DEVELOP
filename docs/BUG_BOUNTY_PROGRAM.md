# Bug Bounty Program

## Purpose
Define scope, safe-harbor boundaries, and evidence requirements for Q5.

## Scope
- Router v1 and reference client v1.
- DEX v0 invariants and receipt replay integrity.

## Non-Scope
- Production bridge or on/off implementations.
- External infrastructure outside this repository.

## MUST
- Submissions MUST include deterministic reproduction steps.
- Evidence MUST include command output and hashes.
- Report MUST specify impacted invariant and scope.

## MUST NOT
- Do not include secrets or sensitive materials in reports.
- Do not test against third-party systems.

## Evidence / Verification
- Use commands in `docs/AUDIT_REPRO_COMMANDS.md`.
- Provide failing output excerpts and minimal inputs.

## Freeze & Change Control
- Changes follow `docs/CHANGE_CONTROL.md`.
