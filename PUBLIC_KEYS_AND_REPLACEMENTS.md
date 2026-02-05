# Production Key Replacement + Public Endpoints

This file records **non-production** API keys and “public key” defaults currently used for development, plus the **public endpoints** in use.

**MUST** replace these values before production launch:
- rotate keys with the provider
- update secrets in deployment (do not commit real keys into git)
- confirm `/capabilities` and the UI reflect the production integration status

## Current keys (dev/test)

### 0x API (EVM swap quotes)
- Env var: `NYX_0X_API_KEY`
- Current dev key: `9638584e-b57c-4de7-9e4d-b52a80d5fe6c`
- Replace before prod: **YES**

### Jupiter API (Solana swap quotes)
- Env var: `NYX_JUPITER_API_KEY`
- Current dev key: `5622a43f-9360-4c42-822d-5b22b1fe8ee5`
- Replace before prod: **YES**

### Magic Eden API (NFT)
- Env var: `NYX_MAGIC_EDEN_API_KEY`
- Notes:
  - Solana endpoints are publicly accessible; providing a key can improve rate limits.
  - The project currently uses a **public/shared** Magic Eden API key for both EVM + Solana (per team convention).
  - Keep it out of git anyway so production deployments can swap it cleanly.
- Replace before prod: **YES**

### PayEVM (payments)
- Env var: `NYX_PAYEVM_API_KEY`
- Notes:
  - Currently uses a **public/shared** key (per team convention).
  - Not integrated with Moon yet.
- Replace before prod: **YES**

## Public endpoints in use (dev/test)

These endpoints are the current external API bases for integrations and the Web2 Guard allowlist.

### 0x (EVM swaps)
- Base: `https://api.0x.org`
- Quote: `https://api.0x.org/swap/permit2/quote`
- Header: `0x-api-key` + `0x-version: v2`
- Chain selection: `chainId` query parameter (v2 unified endpoint)

### Jupiter (Solana swaps)
- Base: `https://api.jup.ag`
- Quote: `https://api.jup.ag/swap/v1/quote`
- Header: `x-api-key`

### Magic Eden (NFTs)
- Solana API: `https://api-mainnet.magiceden.dev/v2`
- EVM public API: `https://api-mainnet.magiceden.dev/v4/evm-public`

### PayEVM (fiat onramp)
- Integration currently disabled in `/capabilities` (no endpoint configured in code).
- Define a production endpoint + webhook verification before enabling.

### Web2 Guard allowlist (shared)
- Gatekept hosts include GitHub, CoinGecko, CoinCap, HttpBin, plus the endpoints above.
- Update the allowlist in `apps/nyx-backend-gateway/src/nyx_backend_gateway/gateway.py` before production.

## Operational reminders

- Do not store production keys in `.env.example`.
- Prefer `.env.local` for developer keys (git-ignored) and a secrets manager for production.
- Prefer runtime secrets (CI/CD secrets manager) and local `.env.local` files that are git-ignored.

---

Signed‑off‑by: **Huangjiahao** (delegated) — 2026‑02‑05
