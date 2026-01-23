# Q9 Audit Reproduction Commands

Purpose
- Provide a single, deterministic command set to reproduce Q9 evidence and verify correctness.

Scope
- Compilation, full test suite, conformance drills, and Q9 one-shot evidence export.

Non-Scope
- Production deployment or any live data claims.

Canonical Verification Commands
- python -m compileall packages/l0-identity/src
- python scripts/nyx_run_all_unittests.py
- PYTHONPATH="packages/conformance-v1/src" python -m conformance_v1.runner --out /tmp/nyx_conformance_report.json
- python scripts/q9_repro_one_shot.py

Expected Outputs
- All tests pass with a non-zero TOTAL_TESTS count.
- Conformance runner prints "conformance ok".
- The one-shot script prints deterministic state_hash and receipt_hash prefixes with replay_ok=True.

Freeze and Change Control
- These commands are the canonical reproduction contract for Q9. Any change requires a versioned update and regression evidence.
