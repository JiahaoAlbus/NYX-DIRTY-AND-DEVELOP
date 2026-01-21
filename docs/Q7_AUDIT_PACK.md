# Q7 Audit Pack

Purpose
- Provide a deterministic and reproducible audit entrypoint for Q7.

Scope
- Unit tests, conformance runner, and evidence generation.

Non-Scope
- No protocol changes.
- No UI behavior claims beyond evidence export.

Normative Rules
- The audit pack MUST use the canonical test runner.
- The audit pack MUST run without network access.

Evidence and Verification
- python -m compileall packages/l0-identity/src
- python scripts/nyx_run_all_unittests.py
- PYTHONPATH="packages/conformance-v1/src" python -m conformance_v1.runner --out /tmp/nyx_conformance_report.json

Freeze and Change Control
- Changes require a versioned update and regression evidence.
