# Repo Truth (What Actually Runs)

Date: 2026-02-09

This file is the canonical snapshot of **what runs today**, **what is authoritative**, and **what is reference/stub**. It is intended to prevent drift between claims and the actual execution path.

## Entrypoints (authoritative)

### Gateway API (Web2 guard + deterministic execution)
- Module: `apps/nyx-backend-gateway/src/nyx_backend_gateway/server.py`
- Command:
  ```bash
  export PYTHONPATH="$(pwd)/apps/nyx-backend-gateway/src:$(pwd)/apps/nyx-backend/src"
  python -m nyx_backend_gateway.server --host 127.0.0.1 --port 8091 --env-file .env.example
  ```
- Metrics: `http://127.0.0.1:8091/metrics`

### Backend evidence engine
- Module: `apps/nyx-backend/src/nyx_backend/server.py`
- Used by gateway for evidence generation and deterministic replay.
- Metrics: `http://127.0.0.1:8090/metrics`

### Web Portal (production UI)
- Directory: `nyx-world/`
- Command:
  ```bash
  cd nyx-world
  npm install
  npm run dev
  ```

### iOS App
- Directory: `apps/nyx-ios/`
- Simulator build:
  ```bash
  bash scripts/build_ios_sim_app.sh
  ```
- IPA (requires Xcode account or Team ID):
  ```bash
  export NYX_IOS_TEAM_ID=YOUR_TEAM_ID
  export NYX_IOS_EXPORT_METHOD=development
  bash scripts/build_ios_ipa.sh
  ```

### Extension
- Directory: `packages/extension/`
- Built by `bash scripts/build_release_artifacts.sh`

### Conformance + Verification
- Full end-to-end: `bash scripts/nyx_verify_all.sh --seed 123 --run-id extreme-testnet`
- Conformance suite (CI gate): `bash scripts/nyx_conformance.sh`

## What is authoritative vs reference/stub

### Authoritative (production-path)
- `apps/nyx-backend-gateway/` (gateway + Web2 guard)
- `apps/nyx-backend/` (deterministic evidence engine)
- `nyx-world/` (web portal)
- `apps/nyx-ios/` (iOS app)
- `packages/extension/` (browser extension)
- `scripts/` (verification, release, ops)
- `docs/` (security/ops/runbooks)

### Reference / legacy / non-production
- `attic/apps/nyx-web/` (reference static UI assets)
- `attic/apps/reference-ui/`, `attic/apps/reference-ui-backend/` (reference-only)
- `attic/apps/nyx-first-app/` (sample app, not production)
- `attic/apps/nyx-reference-client/` (reference client)
- `attic/NYX-DIRTY-AND-DEVELOP/` (duplicate snapshot; see `docs/DEAD_CODE_REPORT.md`)

All `attic/` modules are excluded from CI and release packaging by design.

## Languages used
- Python (gateway/backend, tests, scripts)
- TypeScript/JavaScript (web portal, extension, tooling)
- Swift (iOS app)
- Shell (release & verification scripts)
- YAML/JSON/Markdown (CI, configs, docs)

## Dependency roots (source of truth)
- Python: `pyproject.toml`
- Web portal: `nyx-world/package.json`
- Extension: `packages/extension/package.json`
- CI workflows: `ci/` and `.github/workflows/`

## Known limitations / stubs
- PayEVM is disabled pending official endpoints + webhook verification spec (see `docs/EXTREME_GAP_REPORT.md`).
- Mainnet compliance (KYC/AML, privacy/TOS, enterprise secrets management) is documented but not enforced in code here (see `docs/PROD_GO_LIVE.md`).
- Compliance hook exists but is disabled by default (`NYX_COMPLIANCE_ENABLED=false`).
- External quote integrations are best-effort in `scripts/nyx_verify_all.sh` unless `NYX_REQUIRE_EXTERNAL_QUOTES=1` is set.

## Invariants enforced by tests
- Fee must be non-zero for any shared-state mutation.
- Deterministic replay for evidence bundles.
- Web2 guard SSRF/DNS rebinding and response bounds.
- No hidden bypass paths for auth/fees/evidence.
