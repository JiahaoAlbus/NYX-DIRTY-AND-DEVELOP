# Q6 Security Gate Report

Purpose
- Record the Q6 security gate check results and evidence.

Scope
- Gate checks for tests, conformance, and deterministic outputs.

Non-Scope
- Any protocol changes or feature additions.

MUST and MUST NOT
- The gate report MUST list the exact commands executed.
- The gate report MUST NOT include secrets or sensitive material.
- The gate report MUST only contain factual status.

Gate Summary
- Status: Pending
- Date (UTC):
- Operator:

Executed Commands
- `python -m compileall packages/l0-identity/src`
- `python -m unittest discover -s packages/l0-identity/test -p "*_test.py" -v`
- Conformance runner (if applicable):
  - `PYTHONPATH="packages/conformance-v1/src" python -m conformance_v1.runner --out /tmp/nyx_conformance_report.json`

Results
- Test summary:
- PROPERTY_N:
- Conformance report path:

Evidence / Verification
- Evidence entries should be recorded in the Q6 evidence ledger.

Freeze / Change Control
- Execution-only report; no protocol changes.
