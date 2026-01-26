# Backend Runbook (Testnet Beta)

Purpose
- Provide a single, deterministic way to start the NYX backend gateway for local Testnet Beta development.

Scope
- Local development only.
- Deterministic evidence generation and export.

Non-Scope
- Mainnet operation.
- External wallet integration.
- Production hosting guidance.

Commands (Canonical)
1) Start backend (deterministic):
   - `scripts/nyx_backend_dev.sh`
   - Expected output: `READY http://127.0.0.1:8091`

2) Health check:
   - `curl -s http://127.0.0.1:8091/healthz`
   - Expected: `{"ok":true}`

3) Capabilities:
   - `curl -s http://127.0.0.1:8091/capabilities`

Environment
- The backend loads environment variables from `cswdz.env` if present.
- If `cswdz.env` is not present, the backend uses `.env.example` and runs in testnet safe mode.
- Required variables (see `.env.example`):
  - `NYX_TESTNET_TREASURY_ADDRESS`
  - `NYX_PLATFORM_FEE_BPS`
  - `NYX_PROTOCOL_FEE_MIN`

Determinism Rules
- All evidence exports are deterministic for the same inputs.
- No timestamps are embedded in evidence artifacts.

Troubleshooting
- If `READY` is not printed:
  - Check that port 8091 is free.
  - Confirm Python is available (`python3 -V`).
  - Confirm `.env.example` exists in repo root.
- If `/healthz` fails:
  - Ensure the backend process is running.
  - Check `PYTHONPATH` includes backend sources.

Freeze & Change Control
- This runbook is operational guidance only.
- Changes MUST NOT alter protocol or evidence semantics.
