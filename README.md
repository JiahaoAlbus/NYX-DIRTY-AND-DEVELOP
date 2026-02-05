# NYX Testnet Portal
Deterministic, verifiable portal infrastructure with wallet, exchange, chat, store, and evidence replay—wired to real testnet backends (mainnet-equivalent logic; testnet assets only).

## What This Repo Is
- A **full-stack testnet portal** with end-to-end evidence generation and replay.
- A **mainnet-equivalent execution path** (fees, receipts, state hashes) while using testnet assets.
- A **capabilities-driven UI** (no fake buttons; modules are gated by `/capabilities`).

## What This Repo Is NOT
- **Not mainnet production**: compliance (KYC/AML, privacy/TOS), production secrets management, and enterprise SRE are required for mainnet.
- **Not a custody product**: no HSM/secure enclave integration here.
- **Not a PayEVM integration** (waiting on official endpoints + webhook spec).

## Developer Quickstart (Local)
```bash
export PYTHONPATH="$(pwd)/apps/nyx-backend-gateway/src:$(pwd)/apps/nyx-backend/src"
python -m nyx_backend_gateway.server --host 127.0.0.1 --port 8091 --env-file .env.example

cd nyx-world
npm install
npm run dev
```
Open the URL printed by Vite (default `http://localhost:5173`).

## Full End-to-End Verification (Recommended)
```bash
bash scripts/nyx_verify_all.sh --seed 123 --run-id extreme-testnet
bash scripts/nyx_pack_proof_artifacts.sh
```
Evidence output: `docs/evidence/`  
Proof bundle: `release_artifacts/proof/`

## Build Release Artifacts
```bash
bash scripts/build_release_artifacts.sh
```
Outputs: `release_artifacts/` (web zip, backend tarball, extension zip, iOS simulator app, proof bundles, checksums).

## iOS
Simulator:
```bash
bash scripts/build_ios_sim_app.sh
```
Real device IPA (requires Apple Team ID or Xcode login):
```bash
export NYX_IOS_TEAM_ID=YOUR_TEAM_ID
export NYX_IOS_EXPORT_METHOD=development
bash scripts/build_ios_ipa.sh
```

## Monitoring (Free, Strong)
Metrics exporter:
```bash
python scripts/nyx_metrics_exporter.py
```
Grafana + Prometheus panel:
```bash
export GRAFANA_ADMIN_PASSWORD="your-strong-password"
docker compose -f deploy/free-tier/monitoring/docker-compose.yml up -d
```
Docs: `docs/OPS_RUNBOOK_FREE_TIER.md` and `docs/DEPLOYMENT_FREE_TIER.md`.

## Tests & Validation Commands (What Each Does)
| Command | Purpose |
|---|---|
| `bash scripts/nyx_verify_all.sh --seed 123 --run-id extreme-testnet` | Full end-to-end validation (wallet → trade → chat → store → evidence replay). |
| `bash scripts/nyx_pack_proof_artifacts.sh` | Export verifiable proof bundle. |
| `python scripts/nyx_run_all_unittests.py` | Run backend/unit test suite. |
| `python scripts/nyx_smoke_all_modules.py` | Quick smoke check for core modules. |
| `node scripts/nyx_e2ee_dm_roundtrip.mjs` | E2EE chat roundtrip validation. |
| `python scripts/verify_e2ee_storage.py` | Verify ciphertext-only storage (no plaintext leakage). |
| `python scripts/nyx_monitor_local.py` | Threshold-based alerts (API/DB/Evidence). |
| `python scripts/nyx_metrics_exporter.py` | Metrics endpoint for Prometheus/Grafana. |
| `bash scripts/nyx_backup_encrypted.sh` | Strong encrypted backup (AES-256-GCM + PBKDF2). |
| `bash scripts/nyx_restore_encrypted.sh <enc> <out>` | Restore encrypted backup. |

## Documentation (Recommended)
- Product runbook: `docs/PRODUCT_RUNBOOK.md`
- Testnet functionality matrix: `docs/FUNCTIONALITY_MATRIX_TESTNET_V1.md`
- Mainnet parity rules: `docs/MAINNET_PARITY.md`
- Production go-live checklist: `docs/PROD_GO_LIVE.md`
- Evidence model: `docs/EVIDENCE_MODEL.md`

## Governance / Safety
Some paths are frozen. Break-glass only:
`docs/SEALING_AND_BREAK_GLASS.md`

## Security Boundary
Mock/stdlib implementations only; not production-grade cryptography or HSM/keystore.
Invariant summary: `docs/INVARIANTS_AND_GATES.md`.
