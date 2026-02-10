# NYX Security Model

This document describes trust boundaries, threat assumptions, and secure defaults.

## 1) Trust Boundaries

- **Client boundary**: Web/iOS/extension are untrusted; all security decisions are server-side.
- **Gateway boundary**: Gateway validates inputs, enforces fees, and records evidence.
- **Web2 boundary**: Web2 inputs are hostile and must be mediated by the Web2 gateway.
- **Evidence boundary**: Evidence generation must be deterministic and replayable.

## 2) Threat Assumptions

- Malicious clients can forge requests, replay payloads, and attempt bypasses.
- Web2 endpoints may be compromised or return hostile content.
- Network is untrusted; requests may be manipulated.
- Secrets can leak if stored in plaintext or committed to repo.

## 3) Secure Defaults

- **No privileged bypass paths**: no admin mode, no allowlist overrides to skip fees/auth/evidence.
- **Non-zero fee for shared-state mutations**: every mutation costs `fee_total > 0`.
- **Determinism**: no non-deterministic sources in deterministic code paths.
- **Web2 access**: allowlisted hosts only; bounded sizes and timeouts.
- **Web2 SSRF hardening**: DNS rebinding checks + redirect blocking.
- **Wallet ≠ identity**: `account_id` and `wallet_address` are distinct; auth tokens bind to identity only.
- **Compliance gating (optional)**: external compliance decisions occur before deterministic execution and are not part of evidence.

## 4) Key Custody Model

- Testnet keys are for development only.
- Production keys MUST be managed outside git (KMS/secret manager).
- Session secrets must be strong in production; weak defaults allowed only in dev.
- API uses bearer tokens (no cookies); if cookies are introduced, CSRF defenses are mandatory.

## 5) Configuration Hardening

- `NYX_ENV=dev|staging|prod` controls strictness.
- `NYX_PORTAL_SESSION_SECRET` must be long in staging/prod.
- API keys are optional, but if set must pass format validation.
- `NYX_COMPLIANCE_ENABLED` + `NYX_COMPLIANCE_URL` enable compliance gating (fail-closed by default).
- `NYX_OTEL_ENABLED=true` enables OpenTelemetry spans (exported to stdout by default).

## 6) Logging & Redaction

- Never log raw secrets, API keys, or private keys.
- Prefer request_id/run_id for traceability.
- Web2 responses are hashed; raw bodies are not stored.
- API responses include security headers (CSP, HSTS, X-Frame-Options, etc.).

## 7) Supply-Chain & Dependencies

- Depend on pinned versions where possible.
- SBOM generated for releases.
- CodeQL and dependency review must run in CI.
- Secret scanning runs in CI via `scripts/nyx_secret_scan.py`.

## 8) Security Boundaries (Explicit)

- NYX does **not** provide custody.
- NYX does **not** allow fee waivers for shared state.
- Web2 access always mediated by the gateway.
