# Q6 Release Notes (Mainnet)

Purpose
- Provide factual release notes for mainnet readiness.

Scope
- Execution-only notes for mainnet window evidence.

Non-Scope
- Any protocol change or semantic change.

MUST and MUST NOT
- Notes MUST be factual and evidence-based.
- Notes MUST NOT include secrets or sensitive material.

Release Notes
- Status: Go-ready (tag pending after evidence PR merge)
- Tagged commit: pending
- Evidence summary:
  - Tests OK: `Ran 262 tests in 16.055s` (see `docs/execution/Q6_SECURITY_GATE_REPORT.md`)
  - Conformance: `conformance ok` with report `/tmp/nyx_conformance_report.json`
  - Demo: `replay_ok=True` with `docs/execution/q6_demo_out.txt`

Evidence / Verification
- Evidence paths:
  - `docs/execution/Q6_LIVE_RELEASE_REPORT.md`
  - `docs/execution/Q6_PROVENANCE_PACK.md`
  - `docs/execution/Q6_SECURITY_GATE_REPORT.md`

Freeze / Change Control
- Execution-only notes; no protocol changes.
