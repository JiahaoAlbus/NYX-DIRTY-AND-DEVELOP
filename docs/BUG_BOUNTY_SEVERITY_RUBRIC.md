# Bug Bounty Severity Rubric

## Purpose
Define objective severity levels for Q5 reports.

## Scope
- Router v1, reference client v1, and DEX v0 invariants.

## Non-Scope
- Production custody or external infrastructure.

## MUST
- Severity MUST be based on reproducible evidence.
- Reports MUST include scope and impact summary.

## MUST NOT
- Do not infer severity without deterministic reproduction.

## Severity Levels
- Critical: State mutation or replay integrity can be bypassed.
- High: Fee enforcement or determinism can be bypassed.
- Medium: Denial of service or bounds bypass without state loss.
- Low: Non-sensitive correctness issues without state impact.

## Evidence / Verification
- Provide reproduction commands and minimal inputs.
- Reference failing tests or drills.

## Freeze & Change Control
- Changes follow `docs/CHANGE_CONTROL.md`.
