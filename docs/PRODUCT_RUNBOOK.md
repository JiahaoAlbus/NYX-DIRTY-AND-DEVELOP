# NYX Product Runbook (Testnet Release)

This runbook explains how to run NYX locally, verify the full end-to-end loop, and produce release artifacts.

## Prerequisites

- **Python 3.10+**
- **Node.js + npm**
- **jq**
- (Optional) **Xcode** (for iOS Simulator builds)

## 1) One-click end-to-end verification (recommended)

Runs: wallet → faucet → send → exchange → store → E2EE chat → airdrop → evidence replay → proof export.

```bash
bash scripts/nyx_verify_all.sh --seed 123 --run-id extreme-testnet
bash scripts/nyx_pack_proof_artifacts.sh
```

Outputs:
- Evidence folder: `docs/evidence/<timestamp>_extreme-testnet/verify_all/`
- Latest pointer: `docs/evidence/last_verify_path.txt`
- Proof bundle: `release_artifacts/proof/nyx-proof-<timestamp>.tar.gz`

## 2) Start the backend (manual)

The verification script auto-starts the backend if it is offline. If you prefer manual:

```bash
export PYTHONPATH="$(pwd)/apps/nyx-backend-gateway/src:$(pwd)/apps/nyx-backend/src"
python -m nyx_backend_gateway.server --host 127.0.0.1 --port 8091 --env-file .env.example
```

Optional (external integrations):
- Set `NYX_0X_API_KEY` and `NYX_JUPITER_API_KEY` to enable `GET /integrations/v1/0x/quote` and `GET /integrations/v1/jupiter/quote`.
- Key inventory + replacement checklist: `docs/PUBLIC_KEYS_AND_REPLACEMENTS.md`.

Health check:
```bash
curl -sS http://127.0.0.1:8091/healthz | jq .
curl -sS http://127.0.0.1:8091/capabilities | jq .
```

## 3) Run the web portal (dev)

```bash
cd nyx-world
npm install
npm run dev
```

Open the URL printed by Vite (default `http://localhost:5173`).

Notes:
- dApp Browser is capability-gated (`dapp.browser`) and can open dApps in a new tab (recommended for wallet extension injection).

## 4) iOS (Simulator)

Open `apps/nyx-ios/NYXPortal.xcodeproj` in Xcode and Run, or use:

```bash
xcodebuild -project apps/nyx-ios/NYXPortal.xcodeproj -scheme NYXPortal -destination 'generic/platform=iOS Simulator' build
```

Notes:
- Wallet flows are native (balances/faucet/send).
- Trade/Chat/Store/Proof are embedded web modules with session token injection.
- IPA export requires Apple Developer signing; this repo only produces a simulator `.app` by default.

## 5) Build release artifacts (web + backend + iOS + proof)

```bash
bash scripts/build_release_artifacts.sh
```

Outputs are written under `release_artifacts/` (web zip, backend tarball, extension zip, iOS `.app`, proof tarballs, checksums).
