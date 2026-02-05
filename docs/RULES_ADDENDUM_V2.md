# NYX Rules Addendum V2 (Testnet Portal)

This addendum introduces auxiliary rules for the Testnet Portal v1 implementation. These rules are additive and do not override the Q1 Frozen specs.

## **NX-V2-1: UI Determinism**
- All UI surfaces MUST reflect the real-time state of the backend gateway.
- Fabricating data or using placeholders for critical values (balances, hashes, receipts) is strictly prohibited.

## **NX-V2-2: Error Mediation**
- The gateway MUST NOT expose stack traces or internal system details to the client.
- All errors MUST be mediated into structured JSON responses with descriptive, non-leaking messages.

## **NX-V2-3: Pagination Invariants**
- All listing endpoints MUST support `limit` and `offset` (or `after`) parameters to prevent resource exhaustion and ensure a performant UX.

## **NX-V2-4: Extension Security**
- The browser extension MUST use WebCrypto for all cryptographic operations.
- Private keys MUST be stored in encrypted form within the browser's secure storage.

## **NX-V2-5: Production Key Hygiene**
- Public/shared API keys MUST NOT be used in production.
- Production keys MUST be stored in a secrets manager with least privilege access.
- Production keys MUST be rotated before launch and on security incidents.

## **NX-V2-6: Operational Safety (Mainnet)**
- Production deployments MUST implement monitoring + alerting for API, DB, and wallet operations.
- Production deployments MUST implement backup + restore procedures with defined RPO/RTO targets.
- Production deployments MUST redact secrets and sensitive data from logs.
