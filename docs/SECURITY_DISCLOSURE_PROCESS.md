# Security Disclosure Process

## Purpose
Define the disclosure process for Q5 security reports.

## Scope
- Router v1, reference client v1, and DEX v0 invariants.

## Non-Scope
- Third-party infrastructure and external systems.

## MUST
- Reports MUST include deterministic reproduction steps.
- Reports MUST include evidence and affected invariants.
- Fixes MUST include regression tests or drills.

## MUST NOT
- Do not publish unpatched vulnerabilities.
- Do not include secret material in reports.

## Evidence / Verification
- Use `docs/AUDIT_REPRO_COMMANDS.md` for reproduction.
- Provide minimal input data and outputs.

## Freeze & Change Control
- Changes follow `docs/CHANGE_CONTROL.md`.
