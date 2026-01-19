# Q6 Provenance Pack

Purpose
- Record provenance evidence for Q6 release artifacts and commands.

Scope
- Artifact hashes, command outputs, and lineage references.

Non-Scope
- Any protocol change or semantic change.

MUST and MUST NOT
- Provenance MUST include deterministic hashes and command outputs.
- Provenance MUST NOT include secrets or sensitive material.

Release Anchor
- HEAD: `9e795f461931301344445286e463ce2450fc9a6c`
- Describe: `testnet-0.2-68-g9e795f4`

Provenance Entries
- Artifact: `/tmp/q6_compileall.txt`
  Hash: `e606bfd8da1723f165c1462c95766a2d7bbf231bb6ef49949314b9b37168fd16`
  Source command: `python -m compileall packages/l0-identity/src`
  Output summary: `Listing 'packages/l0-identity/src'...` (no errors)

- Artifact: `/tmp/q6_tests.txt`
  Hash: `853e85e13c1038c91704c82c15b870218df6504f693061b86c0146c19af1cf4b`
  Source command: `python -m unittest discover -s packages/l0-identity/test -p "*_test.py" -v`
  Output summary: `Ran 262 tests in 16.055s` and `OK`; `PROPERTY_N=2000`

- Artifact: `docs/execution/q6_demo_out.txt`
  Hash: `a37f600b3441821e69e430f3bf9b7373f4fedecab515674eb2d3716f8cf7d688`
  Source command: `python packages/e2e-private-transfer/src/e2e_private_transfer/run_demo.py --out /tmp/nyx_q6_private_trace.json --seed 123`
  Output summary: `fee_total=390 tx_hash=5ef0ff12c065 block_hash=5d6a7bb290f4 state_root=b7e876a7e0b2 receipt_hash=6b9e84d92d66 replay_ok=True`

- Artifact: `docs/execution/q6_e2e_demo_trace.json`
  Hash: `8f4abee0fabef51ea7e79137b576cf4c7e8bb6a8b6f80775d090fb36684ad6ed`
  Source command: `python packages/e2e-private-transfer/src/e2e_private_transfer/run_demo.py --out /tmp/nyx_q6_private_trace.json --seed 123`
  Output summary: Deterministic demo trace summary (no secrets)

- Artifact: `/tmp/nyx_conformance_report.json`
  Hash: `25c4e5ad5086ef44111d5c50862669ff93899f40b1c33c7515d5608fedbedff8`
  Source command: `PYTHONPATH="packages/conformance-v1/src" python -m conformance_v1.runner --out /tmp/nyx_conformance_report.json`
  Output summary: `conformance ok`

Evidence / Verification
- Canonical commands are listed in `docs/AUDIT_REPRO_COMMANDS.md`.

Freeze / Change Control
- Execution-only evidence; no protocol changes.
