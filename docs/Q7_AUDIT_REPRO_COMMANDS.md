# Q7 Audit Reproduction Commands

Purpose
- Provide the canonical commands to run Q7 tests and evidence generation deterministically.

Scope
- Test execution and conformance runner invocation.

Non-Scope
- No protocol changes or runtime services.

Commands
- Compile check:
  - python -m compileall packages/l0-identity/src
- Canonical unit tests:
  - python scripts/nyx_run_all_unittests.py
- Conformance runner:
  - PYTHONPATH="packages/conformance-v1/src" python -m conformance_v1.runner --out /tmp/nyx_conformance_report.json

Evidence and Verification
- The unit test runner prints TOTAL_TESTS and exits non-zero on failure.
- The conformance runner exits non-zero on failure and writes the report.

Freeze and Change Control
- Changes require a versioned update and regression evidence.
