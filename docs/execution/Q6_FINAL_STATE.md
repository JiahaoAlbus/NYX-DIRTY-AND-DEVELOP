# Q6 Final State

Purpose
- Record the final state summary for Q6 execution.

Scope
- Final status, evidence pointers, and canonical verification command.

Non-Scope
- Any protocol change or semantic change.

MUST and MUST NOT
- The final state MUST list the canonical verification command.
- The final state MUST NOT include secrets or sensitive material.

Final Summary
- Status: Go
- Date (UTC): 2026-01-19
- Operator: local execution (no CI)
- Tag decision: Mainnet (tag `mainnet-1.0` created)

Canonical Verification Command
- `python -m compileall packages/l0-identity/src`
- `python -m unittest discover -s packages/l0-identity/test -p "*_test.py" -v`
- `PYTHONPATH="packages/conformance-v1/src" python -m conformance_v1.runner --out /tmp/nyx_conformance_report.json`

Evidence / Verification
- Evidence artifacts are listed under `docs/execution/`.
- Demo evidence: `docs/execution/q6_demo_out.txt`, `docs/execution/q6_e2e_demo_trace.json`

Mainnet Tag Commands (maintainer)
- Executed:
  - `git tag -a mainnet-1.0 -m "NYX mainnet-1.0 (sealed semantics; evidence in docs/execution)" 9e795f461931301344445286e463ce2450fc9a6c`
  - `git push origin mainnet-1.0`
- Tag object SHA: `3cca7378cfab588ce3a5fad0da93b3995df8b1de`
- Tagged commit: `9e795f461931301344445286e463ce2450fc9a6c`

Freeze / Change Control
- Execution-only report; no protocol changes.
