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
- Status: Completed
- Date (UTC): 2026-01-19
- Operator: local execution (no CI)

Executed Commands
- `python -m compileall packages/l0-identity/src`
- `python -m unittest discover -s packages/l0-identity/test -p "*_test.py" -v`
- Conformance runner (if applicable):
  - `PYTHONPATH="packages/conformance-v1/src" python -m conformance_v1.runner --out /tmp/nyx_conformance_report.json`

Results
- Test summary: `Ran 262 tests in 16.055s` and `OK`
- PROPERTY_N: `PROPERTY_N=2000` (observed in test output)
- Conformance report path: `/tmp/nyx_conformance_report.json`
- Conformance report hash (sha256): `25c4e5ad5086ef44111d5c50862669ff93899f40b1c33c7515d5608fedbedff8`
- Test log path: `/tmp/q6_tests.txt` (sha256 `853e85e13c1038c91704c82c15b870218df6504f693061b86c0146c19af1cf4b`)
- Compile log path: `/tmp/q6_compileall.txt` (sha256 `e606bfd8da1723f165c1462c95766a2d7bbf231bb6ef49949314b9b37168fd16`)

Evidence / Verification
- Evidence entries should be recorded in the Q6 evidence ledger.

Freeze / Change Control
- Execution-only report; no protocol changes.
