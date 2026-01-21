# Q7 Audit Reproduction Commands

Purpose
- Provide the canonical commands to run Q7 tests and evidence generation deterministically.

Scope
- Test execution, conformance runner invocation, and evidence generation.

Non-Scope
- No protocol changes.
- No network dependencies.

Commands
- Compile check:
  - python -m compileall packages/l0-identity/src
- Canonical unit tests:
  - python tools/nyx_run_all_unittests.py
- Conformance runner:
  - PYTHONPATH="packages/conformance-v1/src" python -m conformance_v1.runner --out /tmp/nyx_conformance_report.json
- One-shot reproduction:
  - scripts/q7_repro_one_shot.sh

Evidence and Verification
- The unit test runner prints TOTAL_TESTS and exits non-zero on failure.
- The conformance runner exits non-zero on failure and writes the report.
- The one-shot script prints:
  - state_hash
  - receipt_hashes
  - replay_ok
- The export bundle is written to:
  - /tmp/nyx_q7_repro_export.zip

Freeze and Change Control
- These commands are normative for Q7 audits.
- Changes require a versioned update and regression evidence.
