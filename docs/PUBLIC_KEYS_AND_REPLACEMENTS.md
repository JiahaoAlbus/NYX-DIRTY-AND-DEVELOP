# Public/Test Keys & Replacement Checklist

This file records **non-production** API keys and “public key” defaults currently used for development.

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
  - The project currently uses a **public/shared** Magic Eden API key for both EVM + Solana (per team convention).
  - Keep it out of git anyway so production deployments can swap it cleanly.
- Replace before prod: **YES**

### PayEVM (payments)
- Env var: `NYX_PAYEVM_API_KEY`
- Notes:
  - Currently uses a **public/shared** key (per team convention).
  - Not integrated with Moon yet.
- Replace before prod: **YES**

## Operational reminders

- Do not store production keys in `.env.example`.
- Prefer runtime secrets (CI/CD secrets manager) and local `.env.local` files that are git-ignored.
