# Q6 Live Release Report

Purpose
- Record evidence for the live release execution in Q6.

Scope
- Release execution steps, evidence, and final outcome.

Non-Scope
- Any protocol change or semantic change.

MUST and MUST NOT
- The report MUST contain objective evidence of each release step.
- The report MUST NOT include secrets or sensitive material.

Release Summary
- Status: Executed (evidence captured)
- Date (UTC): 2026-01-19
- Operator: local execution (no CI)
- Tag decision: Mainnet (tag `mainnet-1.0` created)

Executed Steps
- Step: Compile
  Command or procedure: `python -m compileall packages/l0-identity/src`
  Output summary: `Listing 'packages/l0-identity/src'...` (no errors)
  Evidence reference: `/tmp/q6_compileall.txt` (sha256 `e606bfd8da1723f165c1462c95766a2d7bbf231bb6ef49949314b9b37168fd16`)
- Step: Full tests
  Command or procedure: `python -m unittest discover -s packages/l0-identity/test -p "*_test.py" -v`
  Output summary: `Ran 262 tests in 16.055s` and `OK`; `PROPERTY_N=2000`
  Evidence reference: `/tmp/q6_tests.txt` (sha256 `853e85e13c1038c91704c82c15b870218df6504f693061b86c0146c19af1cf4b`)
- Step: Conformance runner
  Command or procedure: `PYTHONPATH="packages/conformance-v1/src" python -m conformance_v1.runner --out /tmp/nyx_conformance_report.json`
  Output summary: `conformance ok`
  Evidence reference: `/tmp/nyx_conformance_report.json` (sha256 `25c4e5ad5086ef44111d5c50862669ff93899f40b1c33c7515d5608fedbedff8`)
- Step: Deterministic demo
  Command or procedure: `python packages/e2e-private-transfer/src/e2e_private_transfer/run_demo.py --out /tmp/nyx_q6_private_trace.json --seed 123`
  Output summary: `fee_total=390 tx_hash=5ef0ff12c065 block_hash=5d6a7bb290f4 state_root=b7e876a7e0b2 receipt_hash=6b9e84d92d66 replay_ok=True`
  Evidence reference: `docs/execution/q6_demo_out.txt` (sha256 `a37f600b3441821e69e430f3bf9b7373f4fedecab515674eb2d3716f8cf7d688`)

Evidence / Verification
- Canonical commands are listed in `docs/AUDIT_REPRO_COMMANDS.md`.
- Demo trace summary: `docs/execution/q6_e2e_demo_trace.json` (sha256 `8f4abee0fabef51ea7e79137b576cf4c7e8bb6a8b6f80775d090fb36684ad6ed`)
- Tag evidence:
  - Tag: `mainnet-1.0`
  - Tag object SHA: `3cca7378cfab588ce3a5fad0da93b3995df8b1de`
  - Tagged commit: `9e795f461931301344445286e463ce2450fc9a6c`

Freeze / Change Control
- Execution-only report; no protocol changes.
