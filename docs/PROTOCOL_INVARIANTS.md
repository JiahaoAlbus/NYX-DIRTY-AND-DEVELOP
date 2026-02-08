# NYX Protocol Invariants (Testnet Release)

This document defines rules that MUST/MUST NOT hold across **backend**, **web**, **iOS**, and **scripts**.

## 1) Capabilities-driven UI (single source of truth)

- UI MUST fetch `GET /capabilities` on startup and treat it as the source of truth for module availability.
- UI MUST NOT render a state-mutating action as “clickable” when its capability is missing or disabled.
- When a capability is missing/disabled, UI MUST disable or hide the action and MUST surface a human-readable reason (tooltip/title + copy).

## 1.5) Wallet != Identity

- Account identity (handle/public key) MUST NOT be treated as the wallet address.
- The derived `account_id` MUST remain distinct from the user-visible handle.
- UI MUST NOT infer wallet address from handle alone; it must use authenticated account IDs or explicit wallet addresses.

## 2) NO FAKE UI

- Any visible UI control that implies a state mutation MUST either:
  - successfully hit a real backend endpoint and refresh state, OR
  - be disabled/hidden with an explicit reason.
- UI MUST NOT ship “demo-only” buttons, static JSON stubs, or no-op handlers in the primary user path.

## 3) Determinism: `{seed, run_id}` for protocol mutations

- Every protocol state mutation MUST include explicit `seed` and `run_id`.
  - Web: `nyx-world/api.ts` constructs `/run` payloads including `{seed, run_id}`.
  - Scripts: `scripts/nyx_verify_all.sh` generates deterministic run IDs and passes them into every mutation.
  - iOS: native wallet mutations pass run IDs and seed via settings/session.
- `run_id` MUST match `[A-Za-z0-9_-]{1,64}`.
- Implementations MUST NOT depend on wall-clock time to produce deterministic protocol effects.

## 4) Evidence integrity

- Every protocol state mutation MUST generate an evidence bundle that includes:
  - canonical inputs (seed/module/action/payload),
  - outputs (including `state_hash`, `receipt_hashes`, `replay_ok`),
  - stdout summary.
- Evidence MUST be replay-verifiable (`POST /evidence/v1/replay`) and MUST return a diff on mismatch.
- Evidence exports MUST be reproducible:
  - single-run export via `/export.zip?run_id=...`
  - multi-run proof pack via `/proof.zip?prefix=...`

### 4.1 State hash derivation (testnet v1)

- `state_hash` and `receipt_hashes` MUST vary deterministically as a function of `(seed, module, action, payload)`.
- Evidence MUST NOT return static placeholder hashes across different actions.
- Current implementation derives hashes by combining protocol trace outputs with a canonical input fingerprint:
  - `apps/nyx-backend/src/nyx_backend/evidence.py:run_evidence()`

## 5) Economic invariants (fees)

- Every protocol state mutation MUST charge a non-zero fee (protocol + platform).
- Fees MUST be denominated in `NYXT` (testnet token) and MUST be routed to the backend-configured fee address.
- Mutations MUST fail with a clear error when the payer cannot cover fees.
- Wallet transfers MUST enforce:
  - `amount` in `asset_id`,
  - `fee_total` in `NYXT` (even when transferring non-NYXT assets).

## 6) Chat: E2EE invariants (DM v1)

- Clients MUST encrypt message content before sending.
- Backend MUST store only ciphertext envelope (no plaintext).
- Encryption envelope MUST include:
  - `iv` (base64),
  - `ciphertext` (base64),
  - version/algorithm metadata (for forward compatibility).
- Nondeterministic data (e.g. random AES-GCM IV) MUST be included in the message payload so evidence replay remains deterministic.

Current web algorithm (v1):
- Key agreement: ECDH P-256
- Content encryption: AES-256-GCM with random 96-bit IV
- Envelope: JSON `{ v, alg, iv, ciphertext }` (`nyx-world/api.ts:encryptMessage()` / `decryptMessage()`).

## 7) Error handling / hardening

- Backend MUST return structured errors (`{ error: { code, message, details } }`) and MUST NOT leak internal stack traces.
- Retry behavior MUST be limited to idempotent requests (GET/HEAD); state mutations MUST NOT be automatically retried by clients.

## 8) External integrations (0x / Jupiter / etc.)

- External quote endpoints (e.g. `GET /integrations/v1/0x/quote`, `GET /integrations/v1/jupiter/quote`) are **read-only** and MAY be nondeterministic.
- Protocol state mutations MUST NOT depend on an external quote unless a **quote witness** is recorded:
  - The upstream response (or its hash + full response stored as an evidence artifact) MUST be included in the evidence bundle.
  - The evidence inputs MUST include provider name + canonical request parameters used to obtain the quote.
- API keys MUST be provided via environment/deployment secrets and MUST NOT be committed into git.

## 9) Web2 Guard invariants

- Web2 Guard MUST accept only allowlisted HTTPS hosts + path prefixes.
- Web2 Guard MUST reject IP literals, custom ports, and userinfo in URLs.
- Web2 Guard MUST block DNS rebinding and deny hosts that resolve to private/loopback ranges.
- Web2 Guard MUST reject redirects (no follow), including cross-host redirects.
- Web2 Guard MUST cap request bodies and response bytes; truncation MUST be flagged in metadata.
- Web2 Guard MUST store only request/response hashes and ciphertext for secrets (when provided); plaintext secrets MUST NOT be stored.
- Every Web2 Guard request MUST generate evidence with `request_hash`, `response_hash`, `response_status`, and `response_truncated`.
- Web2 Guard MUST charge a non-zero fee routed to treasury and MUST fail with a clear error when balance is insufficient.
