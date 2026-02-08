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
- Add a **compliance service** that issues capability flags.
- Block account actions until compliance is satisfied.
- Record compliance decisions as evidence (without exposing PII).

## 5) Testnet vs Mainnet

- Testnet uses valueless assets and testnet infrastructure.
- Mainnet requires compliance obligations, legal review, and production-grade controls.

## 6) Disclaimer

NYX does not provide legal advice.  
Operators are responsible for meeting jurisdictional requirements.
