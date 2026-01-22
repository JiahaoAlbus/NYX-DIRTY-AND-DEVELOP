# Q8 Audit Reproduction Commands

Purpose
- Provide a single, deterministic command set to reproduce Q8 evidence and checks.

Scope
- Compilation, unit tests, conformance drills, and one-shot evidence generation.

Non-Scope
- UI runtime hosting or production deployment.

Canonical Verification
- python -m compileall packages/l0-identity/src
- python scripts/nyx_run_all_unittests.py
- PYTHONPATH="packages/conformance-v1/src" python -m conformance_v1.runner --out /tmp/nyx_conformance_report.json

One-Shot Evidence
- python scripts/q8_repro_one_shot.py

Freeze and Change Control
- These commands are immutable for Q8 verification. Any change requires explicit versioning and regression evidence.
