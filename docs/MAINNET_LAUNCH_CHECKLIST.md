# Mainnet Launch Checklist

Status: Go/No-Go

## Purpose
Define objective Go/No-Go criteria for the DEX v0 launch process.

## Scope
- DEX v0 implementation, tests, and conformance drills.
- Release gating and evidence capture.

## Non-Scope
- Any change to sealed Q1–Q3 semantics.
- Any new protocol semantics after freeze.

## Go/No-Go Criteria (Objective)
All items MUST be satisfied for Go:
- 0 Critical open issues AND 0 High open issues across audit, bounty, and internal tracking.
- Full test suite green with repo-standard command.
- Property tests green at repo PROPERTY_N.
- Bounded explorer green within defined bounds.
- Conformance v3 drills green.
- Determinism guards green.
- Audit pack complete and reviewed.
- Runbooks complete and reviewed.
- Key ceremony plan complete and reviewed.
- OPSEC model complete and reviewed.
- Release process complete and reviewed.
- Q4 immutable rules index complete.

If any item fails, status MUST be No-Go with blocking items listed.

## Evidence / Verification
Required commands:
- `python -m compileall packages/l0-identity/src`
- `python -m unittest discover -s packages/l0-identity/test -p "*_test.py" -v`

Record:
- Test output summary with counts.
- PROPERTY_N value used.
- Bounded explorer bounds and pass/fail.
- Conformance v3 report path.

## Q5 Additions (Additive Only)
- Router v1 receipt and replay tests MUST be green.
- Reference client output MUST be deterministic for identical seeds.
- Bug bounty and disclosure docs MUST be complete and current.
- Q5 audit reproduction commands MUST be available and verified.

## Freeze / Change Control
- Changes after freeze must follow `docs/CHANGE_CONTROL.md`.
- Semantic changes require a new protocol version and deployment.

## Status (Fill at Release)
- Status: Go | No-Go
- Blocking items (if No-Go):
  - 
