# NYX Mainnet Parity (Testnet v1)

This document defines what “mainnet-equivalent” means for this Testnet Release, and the **only intended differences**.

## 1) The only intended differences

1. **Asset value + faucet**
   - Testnet uses **NYXT/ECHO/USDX** (no real-world value) and provides a faucet (`/wallet/v1/faucet`).
   - Mainnet will use value-bearing assets and **MUST NOT** ship with an unrestricted faucet.

2. **Network identifiers**
   - Testnet may use different chain IDs / addresses / endpoints, but **must preserve** the same UX guarantees:
     fees, receipts, evidence bundles, replay verify, and capability gating.

3. **Integration keys / rate limits**
   - Testnet may use dev/test API keys and more permissive limits for third-party integrations.
   - Mainnet MUST use production keys stored as deployment secrets (never committed into git).

## 2) Parity guarantees (must remain identical)

1. **Capabilities-driven UI**
   - UI MUST render modules/actions based on backend `GET /capabilities`.
   - Missing capability MUST disable/hide actions with a user-visible reason (NO FAKE UI).

2. **Fees + treasury routing**
   - Every protocol state mutation MUST charge a non-zero fee (protocol + platform) and route it to the treasury address configured by the backend.
   - The fee model is the same on mainnet; only the asset value differs.

3. **Evidence chain (NYX core)**
   - Every protocol state mutation MUST generate an evidence bundle containing inputs/outputs, `state_hash`, `receipt_hashes`, and replay status.
   - Replay verification MUST be available (`POST /evidence/v1/replay`) and exports MUST be available (`/export.zip`, `/proof.zip`).

4. **Determinism**
   - Protocol mutations MUST be executed with an explicit `{seed, run_id}` and recorded as evidence.
   - Any nondeterministic data (e.g. random IV for chat encryption) MUST be included in the recorded inputs so replay remains deterministic.

5. **E2EE chat**
   - Client MUST encrypt before sending; backend MUST store ciphertext envelope only (no plaintext).
   - Key agreement + encryption algorithms MUST remain the same between testnet and mainnet.

## 3) Explicit non-parity (disabled in testnet v1)

- Web2 Guard: capability-disabled (`web2.guard = disabled`) until deterministic signing + policy are implemented.
- Fiat on-ramp: not shipped in this repo; must remain disabled (no fake “Buy” buttons).
