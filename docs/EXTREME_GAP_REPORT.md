# NYX-DIRTY Extreme Gap Report (Full-Stack Audit)

Audit date: **2026-02-04**

Scope: this workspace (`/Users/huangjiahao/Desktop/NYX/nyx`) as a **Testnet Release** baseline with:
- **NO FAKE UI**: UI actions are either wired to real backend state mutations or are disabled/hidden with a reason.
- **Mainnet-equivalent flows**: fees/receipts/evidence/replay logic is identical; only assets have testnet value.
- **Determinism first**: every protocol state mutation uses `{seed, run_id}` and produces evidence.
- **Capabilities-driven UI**: backend `/capabilities` is the single source of truth for module availability.

Legend:
- **🟢 OK**: usable end-to-end, real backend, state refresh, evidence + replay verify.
- **🟡 Limited**: usable but intentionally constrained (e.g. only one trading pair).
- **🔴 Disabled**: capability-disabled and not fake-clickable.

## Cross-cutting audit (global)

| Area | Status | Evidence (code-based) |
|---|---:|---|
| Capabilities-driven UI | 🟢 | Backend: `apps/nyx-backend-gateway/src/nyx_backend_gateway/server.py:_capabilities()`. Web gating: `nyx-world/capabilities.ts`, `nyx-world/App.tsx`, `nyx-world/components/BottomNav.tsx`, `nyx-world/screens/Home.tsx`. |
| Unified API client (timeout/error mapping/retry) | 🟢 | `nyx-world/api.ts:requestJson()` implements timeout + typed `ApiError` + retry only for idempotent methods. |
| Deterministic run IDs (web) | 🟢 | `nyx-world/api.ts:allocateRunId()` uses a monotonic counter keyed by `baseRunId`. |
| Deterministic run IDs (scripts) | 🟢 | `scripts/nyx_verify_all.sh` allocates non-colliding run IDs and writes evidence under `docs/evidence/`. |
| Evidence replay + proof export | 🟢 | `POST /evidence/v1/replay` and `GET /proof.zip?prefix=...` (auth) are implemented in gateway; web exposes “Verify Replay” + proof download. |
| Backend migrations reproducible | 🟢 | `apps/nyx-backend-gateway/src/nyx_backend_gateway/migrations.py` covered by unit tests. |
| NO FAKE UI | 🟢 | Capability-missing modules/actions are disabled with an explanatory tooltip/title (no dead buttons). |

## Module-by-module audit

### 0) Portal / Auth

| UI Entry | Backend endpoint | MutatesState | Evidence | Status | Notes |
|---|---|---:|---:|---:|---|
| Web onboarding | `POST /portal/v1/accounts`, `POST /portal/v1/auth/challenge`, `POST /portal/v1/auth/verify`, `GET /portal/v1/me` | Yes | No | 🟢 | Portal auth is treated as **identity/session state** (explicitly out of the protocol evidence chain). |
| iOS native auth | same | Yes | No | 🟢 | `apps/nyx-ios/Views/PortalAuthView.swift` + `apps/nyx-ios/Network/GatewayClient.swift`. |
| Capabilities bootstrap | `GET /capabilities` | No | No | 🟢 | Web/iOS gate modules from this response. |

### A) Wallet (+ Faucet) — “MetaMask-level”

| UI Entry | Backend endpoint | MutatesState | Evidence | Status | Notes |
|---|---|---:|---:|---:|---|
| Balances / assets | `GET /wallet/v1/balances` | No | No | 🟢 | Multi-asset: NYXT + ECHO + USDX (testnet). |
| Transfer (Send) | `POST /wallet/v1/transfer` | Yes | Yes | 🟢 | Fee enforced + treasury routing; receipt/state_hash returned. |
| Tx history | `GET /wallet/v1/transfers` | No | No | 🟢 | Paginates (`limit/offset`). |
| Faucet | `POST /wallet/v1/faucet` | Yes | Yes | 🟢 | Cooldown/quota errors are structured (e.g. `retry_after_seconds`). |
| iOS native wallet | same | Yes/No | Yes | 🟢 | Native balance/faucet/send implemented (not WebView). |

### B) Exchange / Trade — “Binance Lite”

| UI Entry | Backend endpoint | MutatesState | Evidence | Status | Notes |
|---|---|---:|---:|---:|---|
| Order book | `GET /exchange/orderbook` | No | No | 🟢 | Supports pagination (`limit/offset`) and refresh. |
| Place order | `POST /run` (`exchange:place_order`) | Yes | Yes | 🟢 | Validations: supported pair, bounds, balance + fee checks. |
| Cancel order | `POST /run` (`exchange:cancel_order`) | Yes | Yes | 🟢 | Ownership checks enforced when authenticated. |
| My orders / trades | `GET /exchange/v1/my_orders`, `GET /exchange/v1/my_trades` | No | No | 🟢 | Paginates (`limit/offset`). |
| Pair coverage | N/A | N/A | N/A | 🟡 Limited | Testnet v1 exposes one pair: **ECHO/NYXT** (`/capabilities.exchange_pairs`). |

### C) Store / Marketplace — “Taobao-lite”

| UI Entry | Backend endpoint | MutatesState | Evidence | Status | Notes |
|---|---|---:|---:|---:|---|
| Listings | `GET /marketplace/listings`, `GET /marketplace/listings/search` | No | No | 🟢 | Paginates; empty state supported. |
| Publish listing | `POST /run` (`marketplace:listing_publish`) | Yes | Yes | 🟢 | Seller creates listing; fee enforced. |
| Purchase | `POST /run` (`marketplace:purchase_listing`) | Yes | Yes | 🟢 | Buyer pays + fee; receipt/state_hash returned. |
| My orders | `GET /marketplace/v1/my_purchases` | No | No | 🟢 | Paginates (`limit/offset`). |

### D) Chat — “IG smooth + real E2EE”

| UI Entry | Backend endpoint | MutatesState | Evidence | Status | Notes |
|---|---|---:|---:|---:|---|
| Conversations | `GET /chat/v1/conversations` | No | No | 🟢 | Minimal DM list. |
| E2EE identity | `POST /portal/v1/e2ee/identity`, `GET /portal/v1/accounts/by_id` | Yes/No | No | 🟢 | Identity record stores public key only. |
| Send DM (E2EE) | `POST /run` (`chat:message_event`) | Yes | Yes | 🟢 | Client encrypts (ECDH P-256 → AES-GCM). Backend stores ciphertext envelope only. |
| Message list | `GET /chat/messages?channel=...` | No | No | 🟢 | Pagination supported. |

### E) Faucet / Airdrop (real tasks)

| UI Entry | Backend endpoint | MutatesState | Evidence | Status | Notes |
|---|---|---:|---:|---:|---|
| Airdrop tasks | `GET /wallet/v1/airdrop/tasks` | No | No | 🟢 | Tasks are real: `trade_1`, `chat_1`, `store_1`. |
| Claim | `POST /wallet/v1/airdrop/claim` | Yes | Yes | 🟢 | One-claim-per-task; reward mints NYXT with evidence. |

### F) Evidence Center (NYX core)

| UI Entry | Backend endpoint | MutatesState | Evidence | Status | Notes |
|---|---|---:|---:|---:|---|
| Activity feed | `GET /portal/v1/activity` | No | N/A | 🟢 | Shows receipts for wallet/exchange/store/chat/airdrop. |
| Evidence view | `GET /evidence?run_id=...` | No | N/A | 🟢 | Surfaces inputs/outputs/receipt_hashes/state_hash + fee/treasury fields. |
| Verify replay | `POST /evidence/v1/replay` | No | N/A | 🟢 | Replays recorded evidence and returns a diff (ok/failed). |
| Export (per run) | `GET /export.zip?run_id=...` | No | N/A | 🟢 | Deterministic zip with manifest. |
| Proof package (multi-run) | `GET /proof.zip?prefix=...` | No | N/A | 🟢 | Bundles multiple user-owned runs for reviewers. |

### G) iOS (native wallet + web modules)

| UI Entry | Backend endpoint | MutatesState | Evidence | Status | Notes |
|---|---|---:|---:|---:|---|
| Native wallet + faucet + send | wallet v1 endpoints | Yes/No | Yes | 🟢 | Native pages (no WebView for wallet). |
| Trade / Chat / Store / Proof | Web embed (token injected) | varies | varies | 🟢 | Embedded `nyx-world` with shared session + deep links. |
| Simulator build | N/A | N/A | N/A | 🟢 | `release_artifacts/ios/NYXPortal.app` built via `scripts/build_release_artifacts.sh`. |

### H) dApp Browser

| UI Entry | Backend endpoint | MutatesState | Evidence | Status | Notes |
|---|---|---:|---:|---:|---|
| dApp Browser | (Web-only) | No | No | 🟢 | Capability-enabled (`dapp.browser = enabled`). Opens dApps in a new tab by default; optional iframe embed may be blocked by CSP/XFO. |

### I) External integrations (read-only)

| UI Entry | Backend endpoint | MutatesState | Evidence | Status | Notes |
|---|---|---:|---:|---:|---|
| 0x Quote (EVM) | `GET /integrations/v1/0x/quote` | No | No | 🟡 Limited | Auth required; enabled only when `NYX_0X_API_KEY` is set (`integrations.0x_quote`). |
| Jupiter Quote (Solana) | `GET /integrations/v1/jupiter/quote` | No | No | 🟡 Limited | Auth required; enabled only when `NYX_JUPITER_API_KEY` is set (`integrations.jupiter_quote`). |
| Magic Eden collections (Solana) | `GET /integrations/v1/magic_eden/solana/collections` | No | No | 🟡 Limited | Auth required; enabled only when `NYX_MAGIC_EDEN_API_KEY` is set (`integrations.magic_eden_solana`). |
| Magic Eden listings (Solana) | `GET /integrations/v1/magic_eden/solana/collection_listings` | No | No | 🟡 Limited | Requires `symbol` + pagination; enabled only when `NYX_MAGIC_EDEN_API_KEY` is set. |
| Magic Eden token (Solana) | `GET /integrations/v1/magic_eden/solana/token` | No | No | 🟡 Limited | Requires `mint`; enabled only when `NYX_MAGIC_EDEN_API_KEY` is set. |
| Magic Eden (EVM) / PayEVM | N/A | N/A | N/A | 🔴 Disabled | EVM integration endpoints not shipped; PayEVM not implemented (NO FAKE UI). |

### J) Web2 Guard

| UI Entry | Backend endpoint | MutatesState | Evidence | Status | Notes |
|---|---|---:|---:|---:|---|
| Web2 Guard | `GET /web2/v1/allowlist` | No | N/A | 🟢 | Allowlisted public Web2 endpoints. |
| Web2 Guard request | `POST /web2/v1/request` | Yes | Yes | 🟢 | Deterministic evidence includes request/response hashes + fee routing. |
| Web2 Guard history | `GET /web2/v1/requests` | No | N/A | 🟢 | Paginated request history per account. |

## Remaining disabled features (by design)

| Module | Capability | Status | Reason |
|---|---|---:|---|
| Fiat on-ramp | (no capability in backend) | 🔴 Disabled | No provider integration in this repo; not exposed as a primary flow. |
