# NYX Protocol Invariants

This document defines the immutable rules and logical constraints of the NYX Testnet Ecosystem. These invariants MUST be preserved across all implementations (Web, iOS, Backend).

## 1. Determinism
- **MUST** generate a unique `state_hash` for every sequence of operations given the same `seed` and `run_id`.
- **MUST** produce verifiable evidence for every state transition.
- **MUST NOT** allow non-deterministic factors (system time, random number generators without seeds) to influence state transitions.

## 2. Economic Invariants (Testnet)
- **MUST** apply a non-zero protocol fee to all state-mutating transactions (Exchange, Marketplace, Transfer).
- **MUST** route all fees to the designated treasury address: `0x0Aa313fCE773786C8425a13B96DB64205c5edCBc`.
- **MUST NOT** allow zero-fee transactions to be recorded in the evidence chain.
- **MUST** preserve the "Conservation of Value" (Sum of balances + fees must remain constant within a closed loop).

## 3. Data Integrity
- **MUST NOT** use fake or mock data in any production-like environment.
- **MUST** treat every "Mock" or "Placeholder" as a failure in audit.
- **MUST** ensure that "Identity" (User Handle) is logically separated from "Account" (Deterministic Wallet Address).

## 4. Evidence Integrity
- **MUST** include all input parameters in the `EvidenceBundle`.
- **MUST** allow any third party to replay the sequence of events and verify the `state_hash`.
- **MUST NOT** allow tampering with historical evidence without breaking the hash chain.

## 5. Privacy & Security
- **MUST** encrypt P2P chat messages locally before transmission.
- **MUST NOT** store clear-text authorization keys for Web2 access on the backend.
- **MUST** enforce rate limits at the Gateway level to prevent DDoS while maintaining deterministic order.
