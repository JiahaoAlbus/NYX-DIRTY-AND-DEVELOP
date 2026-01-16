# Release Notes Q5 RC

Purpose
- Record what is included in the Q5 release candidate and how it is verified.

Scope
- Router v1 receipts/replay and reference client v1 output.
- Conformance drills and audit evidence.

Non-Scope
- Mainnet release decision.
- Production bridge or on/off ramp.

MUST and MUST NOT
- This document MUST not claim mainnet readiness.
- Evidence MUST reference deterministic verification commands.
- Any change after RC MUST be patch-only with regression proof.

What Shipped
- Router v1 receipts and deterministic replay.
- Reference client v1 deterministic report output.
- Conformance drills for router and client boundaries.

What Did Not Ship
- Mainnet tag and production deployment.
- Production bridge/on-off integration.

Evidence / Verification
- `python -m compileall packages/l0-identity/src`
- `python -m unittest discover -s packages/l0-identity/test -p "*_test.py" -v`
- Conformance report: `PYTHONPATH="packages/conformance-v1/src" python -m conformance_v1.runner --out /tmp/nyx_conformance_report.json`

Tagging (Requires Maintainer Action)
- `git tag -a q5-rc1 -m "NYX Q5 RC1"`
- `git push origin q5-rc1`

Release Window Status
- No-Go: mainnet tag not authorized.

Freeze / Change Control
- Changes follow `docs/CHANGE_CONTROL.md`.
