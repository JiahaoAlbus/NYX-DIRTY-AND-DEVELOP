# Demo Evidence Pack (Testnet Beta)

Purpose
- Provide a deterministic, auditable evidence pack for fundraising demos without changing protocol semantics.

Scope
- Testnet Beta only.
- Evidence export and replay validation for all modules.

Non-Scope
- Mainnet claims.
- External wallet integration.
- Live network metrics.

Evidence Artifacts
- The evidence bundle MUST include:
  - protocol_anchor
  - inputs
  - outputs
  - receipt_hashes
  - state_hash
  - replay_ok
  - stdout
- Evidence exports MUST be deterministic for identical inputs.

One-Command Demo
- Start backend:
  - `scripts/nyx_backend_dev.sh`
- Run deterministic smoke across modules:
  - `python scripts/nyx_smoke_all_modules.py --seed 123 --run-id demo-run`

Evidence Output Location
- Smoke artifacts are written to:
  - `docs/evidence/smoke/<timestamp>/`

Verification (Required)
- `python -m compileall packages/l0-identity/src`
- `python scripts/nyx_run_all_unittests.py`
- `PYTHONPATH="packages/conformance-v1/src" python -m conformance_v1.runner --out nyx_conformance_report.json`

Freeze & Change Control
- This evidence pack is additive and MUST NOT change existing evidence formats.
