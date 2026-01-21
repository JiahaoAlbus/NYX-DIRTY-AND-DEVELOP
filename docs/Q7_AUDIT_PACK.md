# Q7 Audit Pack

Purpose
- Provide a deterministic and reproducible audit entrypoint for Q7 UI and evidence flows.

Scope
- Unit tests, conformance runner, and evidence generation.
- Evidence generation via the reference backend wrapper.
- Deterministic export bundle and replay confirmation.

Non-Scope
- No protocol changes.
- No UI behavior claims beyond evidence export.

Normative Rules
- The audit pack MUST use the canonical test runner.
- The audit pack MUST provide deterministic reproduction commands.
- The audit pack MUST NOT rely on network access.
- The audit pack MUST include evidence bundle exports and summary outputs.

Evidence and Verification
- Compile check:
  - python -m compileall packages/l0-identity/src
- Canonical unit tests:
  - python tools/nyx_run_all_unittests.py
- Conformance runner:
  - PYTHONPATH="packages/conformance-v1/src" python -m conformance_v1.runner --out /tmp/nyx_conformance_report.json
- One-shot reproduction:
  - scripts/q7_repro_one_shot.sh
- Evidence artifacts:
  - /tmp/nyx_q7_repro
  - /tmp/nyx_q7_repro_export.zip

Freeze and Change Control
- This audit pack is normative for Q7.
- Changes require a versioned update and regression evidence.
