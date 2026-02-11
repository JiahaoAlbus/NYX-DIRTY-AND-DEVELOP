# NYX Compliance Posture

This document states the compliance stance and anti-abuse controls.

## 1) Explicit Statement

NYX **does not facilitate regulatory evasion**.  
The system is designed to support lawful operation and auditability.

## 2) Anti-Abuse Controls

- Rate limits per IP and per account.
- Evidence logging of all state mutations.
- Web2 gateway allowlist with bounds and audit trail.
- Deny policies for suspicious patterns (burst abuse, invalid signatures, repeated failures).

## 3) Data Handling

- Store only what is required for deterministic evidence and auditability.
- Avoid storing secrets in plaintext.
- Maintain retention windows appropriate for jurisdictional requirements.

## 4) KYC/AML Integration Path (Future)

The architecture supports integrating KYC/AML without redesign:
- Add a **compliance service** that issues allow/deny decisions.
- Gate shared-state mutations via `NYX_COMPLIANCE_ENABLED=true`.
- Decisions are evaluated **before** deterministic execution (no PII in evidence).

### Compliance Hook (Current Integration Point)
- `NYX_COMPLIANCE_URL` is called with `{account_id, wallet_address, module, action, run_id, metadata}`.
- `NYX_COMPLIANCE_FAIL_CLOSED=true` blocks actions if the service is unavailable.
- The compliance service is **external** and should implement its own audit log and retention policy.

## 5) Mainnet Compliance Templates

Templates are provided for mainnet rollout:
- `docs/MAINNET_COMPLIANCE_TEMPLATE.md`
- `docs/LEGAL_TEMPLATES_MAINNET.md`

## 6) Testnet vs Mainnet

- Testnet uses valueless assets and testnet infrastructure.
- Mainnet requires compliance obligations, legal review, and production-grade controls.

## 7) Disclaimer

NYX does not provide legal advice.  
Operators are responsible for meeting jurisdictional requirements.
