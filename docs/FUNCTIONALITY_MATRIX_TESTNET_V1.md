# NYX Functionality Matrix (Testnet v1)

This matrix maps **real UI flows** → **real backend endpoints**, including whether the action mutates protocol state and whether it generates **evidence** (`state_hash`, `receipt_hashes`, replay verify).

Source of truth for what should render in UI: `GET /capabilities` (`apps/nyx-backend-gateway/src/nyx_backend_gateway/server.py:_capabilities()`).

Legend:
- **MutatesState**: changes protocol state (wallet/exchange/store/chat/airdrop via `/run` or wallet v1 mutations).
- **Evidence**: evidence bundle exists and can be fetched (`/evidence?run_id=...`) and replay-verified (`/evidence/v1/replay`).
- **Status**: `OK`, `Limited`, or `Disabled (by capabilities)`.

## Capabilities (Testnet v1)

Backend declares (example):
- `wallet`: `faucet`, `transfer`, `airdrop`
- `exchange`: `trading`, `orderbook`
- `marketplace`: `listing`, `purchase`
- `chat`: `e2ee`, `dm`
- `dapp`: `browser` (**enabled**)
- `web2`: `guard` (**enabled**)
- `integrations`: `0x_quote`, `jupiter_quote`, `magic_eden_solana`, `magic_eden_evm`, `payevm` (capability-driven; see `/capabilities`)

## Matrix

| Module | UI Action | Frontend entry | Backend endpoint | MutatesState | Evidence | Status | Notes |
|---|---|---|---|---:|---:|---:|---|
| Portal | Create account | Web `nyx-world/screens/Onboarding.tsx`, iOS `apps/nyx-ios/Views/PortalAuthView.swift` | `POST /portal/v1/accounts` | Yes | No | OK | Identity/session state (explicitly outside protocol evidence chain). |
| Portal | Login | same | `POST /portal/v1/auth/challenge` → `POST /portal/v1/auth/verify` | No | No | OK | Auth tokens gate all protocol actions. |
| Portal | Logout | Web Settings | `POST /portal/v1/auth/logout` | No | No | OK | Clears session token. |
| Meta | Capabilities bootstrap | Web app init, iOS init | `GET /capabilities` | No | No | OK | UI gates modules/actions from this response. |
| Wallet | List balances | Web Wallet, iOS Wallet | `GET /wallet/v1/balances` | No | No | OK | Multi-asset list. |
| Wallet | Faucet claim | Web Faucet, iOS Wallet | `POST /wallet/v1/faucet` | Yes | Yes | OK | Returns updated balance + fee + `run_id` receipts; errors include `retry_after_seconds` when rate-limited. |
| Wallet | Transfer (Send) | Web Wallet, iOS Wallet | `POST /wallet/v1/transfer` | Yes | Yes | OK | Enforces address/amount bounds + fee + treasury routing. |
| Wallet | Transfer history | Web Wallet | `GET /wallet/v1/transfers` | No | No | OK | Pagination (`limit/offset`). |
| Exchange | Order book | Web Trade | `GET /exchange/orderbook` | No | No | OK | Pagination + refresh. |
| Exchange | Place order | Web Trade | `POST /run` (`exchange:place_order`) | Yes | Yes | OK | Pair + precision/bounds + balance checks; fees charged in NYXT. |
| Exchange | Cancel order | Web Trade | `POST /run` (`exchange:cancel_order`) | Yes | Yes | OK | Ownership enforced for authenticated caller. |
| Exchange | My orders | Web Trade | `GET /exchange/v1/my_orders` | No | No | OK | Pagination (`limit/offset`). |
| Exchange | My trades (fills) | Web Trade | `GET /exchange/v1/my_trades` | No | No | OK | Filled trades include `run_id` for evidence lookup. |
| Marketplace | Browse listings | Web Store | `GET /marketplace/listings` | No | No | OK | Pagination + empty state. |
| Marketplace | Search listings | Web Store | `GET /marketplace/listings/search` | No | No | OK | Query + pagination. |
| Marketplace | Publish listing | Web Store | `POST /run` (`marketplace:listing_publish`) | Yes | Yes | OK | Fee charged in NYXT. |
| Marketplace | Purchase listing | Web Store | `POST /run` (`marketplace:purchase_listing`) | Yes | Yes | OK | Fee charged; receipt/state_hash returned. |
| Marketplace | My purchases | Web Store | `GET /marketplace/v1/my_purchases` | No | No | OK | Pagination (`limit/offset`). |
| Chat | List conversations | Web Chat | `GET /chat/v1/conversations` | No | No | OK | Minimal DM list. |
| Chat | Upsert E2EE identity | Web Chat, scripts | `POST /portal/v1/e2ee/identity` | Yes | No | OK | Stores public key material only. |
| Chat | Send E2EE DM | Web Chat | `POST /run` (`chat:message_event`) | Yes | Yes | OK | Client-side E2EE; backend stores ciphertext envelope only. |
| Chat | List messages | Web Chat | `GET /chat/messages?channel=...` | No | No | OK | Pagination. |
| Airdrop | List tasks | Web Airdrop | `GET /wallet/v1/airdrop/tasks` | No | No | OK | Real completion checks: trade/chat/store. |
| Airdrop | Claim task | Web Airdrop | `POST /wallet/v1/airdrop/claim` | Yes | Yes | OK | One claim per task; mints NYXT. |
| Evidence | Activity feed | Web Activity | `GET /portal/v1/activity` | No | N/A | OK | Receipt index for the user. |
| Evidence | View evidence bundle | Web Proof | `GET /evidence?run_id=...` | No | N/A | OK | Shows inputs/outputs/state_hash/receipt_hashes. |
| Evidence | Verify replay | Web Proof | `POST /evidence/v1/replay` | No | N/A | OK | Returns `{ok,diff}` (deterministic verification). |
| Evidence | Export single proof | Web Proof | `GET /export.zip?run_id=...` | No | N/A | OK | Deterministic export zip with manifest. |
| Evidence | Export proof pack | scripts + backend | `GET /proof.zip?prefix=...` | No | N/A | OK | Bundles all runs matching prefix for a user. |
| dApp | Browser | Home card → `nyx-world/screens/DappBrowser.tsx` | N/A (client-side) | No | No | OK | Capability-enabled (`dapp.browser = enabled`). Opens in new tab by default; optional iframe embed may be blocked by CSP/XFO. |
| Integrations | 0x quote (EVM) | (no UI yet) | `GET /integrations/v1/0x/quote` | No | No | Limited | Auth required; enabled only when `integrations.0x_quote` is not disabled. |
| Integrations | Jupiter quote (Solana) | (no UI yet) | `GET /integrations/v1/jupiter/quote` | No | No | Limited | Auth required; enabled only when `integrations.jupiter_quote` is not disabled. |
| Integrations | Magic Eden collections (Solana) | (no UI yet) | `GET /integrations/v1/magic_eden/solana/collections` | No | No | Limited | Public endpoint; optional API key for rate limits. |
| Integrations | Magic Eden listings (Solana) | (no UI yet) | `GET /integrations/v1/magic_eden/solana/collection_listings` | No | No | Limited | Requires `symbol` + pagination; public endpoint, optional API key. |
| Integrations | Magic Eden token (Solana) | (no UI yet) | `GET /integrations/v1/magic_eden/solana/token` | No | No | Limited | Requires `mint`; public endpoint, optional API key. |
| Web2 | Guard | Home card → Web2 Guard | `GET /web2/v1/allowlist`, `POST /web2/v1/request`, `GET /web2/v1/requests` | Yes (request) | Yes | OK | Allowlisted HTTPS only; response hash captured in evidence; secrets stored as ciphertext. |
| Fiat | On-ramp | (not exposed) | N/A | N/A | N/A | Disabled | No provider integration; screen is not part of the primary flow. |
