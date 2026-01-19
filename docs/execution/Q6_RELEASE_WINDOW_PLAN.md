# Q6 Release Window Plan

Purpose
- Define the operational plan for Q6 release execution.

Scope
- Release window sequencing, evidence capture, and Go/No-Go checkpoints.

Non-Scope
- Any protocol changes or new features.

MUST and MUST NOT
- Each release step MUST record evidence hashes and command outputs.
- Release MUST NOT proceed without objective Go status.
- If No-Go, the process MUST stop and record blockers.

Execution Phases
1) Pre-flight
- Run canonical verification commands.
- Record PROPERTY_N and test summary.

2) Evidence Capture
- Capture conformance report output path.
- Capture client and router deterministic outputs.

3) Decision Gate
- Update MAINNET_LAUNCH_CHECKLIST status based on evidence.

Evidence / Verification
- `python -m compileall packages/l0-identity/src`
- `python -m unittest discover -s packages/l0-identity/test -p "*_test.py" -v`
- Conformance report: `PYTHONPATH="packages/conformance-v1/src" python -m conformance_v1.runner --out /tmp/nyx_conformance_report.json`

Freeze / Change Control
- Execution-only; no semantic changes.
