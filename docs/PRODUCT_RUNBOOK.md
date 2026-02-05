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
- Set keys in `.env.local` (recommended) or export env vars directly.
- `NYX_0X_API_KEY` → enables `GET /integrations/v1/0x/quote`.
- `NYX_JUPITER_API_KEY` → enables `GET /integrations/v1/jupiter/quote`.
- `NYX_MAGIC_EDEN_API_KEY` → optional (public endpoints work without it; key can improve rate limits).
- Magic Eden EVM endpoints:
  - `GET /integrations/v1/magic_eden/evm/collections/search`
  - `GET /integrations/v1/magic_eden/evm/collections`
- Key inventory + replacement checklist: `PUBLIC_KEYS_AND_REPLACEMENTS.md`.

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
- Web2 Guard is capability-gated (`web2.guard`). It only allows allowlisted HTTPS endpoints and records request/response hashes in evidence.
- Default allowlist includes 0x, Jupiter, Magic Eden, GitHub, CoinGecko, CoinCap, and HttpBin (see `/web2/v1/allowlist`).

Web2 Guard quick check:
```bash
curl -sS http://127.0.0.1:8091/web2/v1/allowlist | jq .
```

## 4) iOS (Simulator)

Open `apps/nyx-ios/NYXPortal.xcodeproj` in Xcode and Run, or use:

```bash
xcodebuild -project apps/nyx-ios/NYXPortal.xcodeproj -scheme NYXPortal -destination 'generic/platform=iOS Simulator' build
```

Notes:
- Wallet flows are native (balances/faucet/send).
- Trade/Chat/Store/Proof are embedded web modules with session token injection.
- Web2 Guard can be opened from Home → Web2 Guard (web module).
- IPA export requires Apple Developer signing; this repo only produces a simulator `.app` by default.

## 4b) iOS (Real Device / IPA)

To produce an **installable iPhone IPA**, you must sign with an Apple Developer Team ID.

```bash
export NYX_IOS_TEAM_ID=YOUR_TEAM_ID
export NYX_IOS_EXPORT_METHOD=development   # or ad-hoc / app-store / enterprise
bash scripts/build_ios_ipa.sh
```

Output:
- `release_artifacts/ios/NYXPortal.ipa`

Install:
- Xcode → Devices & Simulators → drag IPA, or
- Apple Configurator / `ideviceinstaller` (for ad-hoc).

## 5) Build release artifacts (web + backend + iOS + proof)

```bash
bash scripts/build_release_artifacts.sh
```

Outputs are written under `release_artifacts/` (web zip, backend tarball, extension zip, iOS `.app`, proof tarballs, checksums).
