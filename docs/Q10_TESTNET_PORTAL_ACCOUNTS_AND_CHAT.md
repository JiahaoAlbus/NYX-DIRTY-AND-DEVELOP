# Q10 Testnet Portal Accounts and Chat (Normative)

Purpose
- Define the portal account model, authentication, session handling, and chat security for Testnet Beta.
- Specify deterministic evidence requirements for interactive flows.

Scope
- Portal access principals for Testnet Beta only.
- Challenge/response authentication without passwords or personal data.
- Chat room creation, message submission, and deterministic receipt chaining.

Non-Scope
- KYC, real-world identity binding, or external wallet connections.
- Mainnet deployment or settlement integration.
- Protocol semantics changes to sealed layers.

Definitions
- Portal Account: a pseudonymous access principal used for portal access only.
- Account ID: server-issued identifier for a portal account.
- Handle: a short, user-chosen label with strict policy and uniqueness.
- Public Key: a base64-encoded public key used for authentication.
- Session: a short-lived access token or server-side session id issued after verification.
- Chat Room: a server-side room that stores message records.
- Message Receipt: a deterministic digest chain that proves message ordering.

Portal Account Model (MUST)
- The account record MUST include: account_id, handle, public_key, created_at, status.
- Handles MUST be unique and validated by length and character policy.
- Public keys MUST be provided as base64 and validated for size and format.
- Accounts MUST be stored in persistent storage (no in-memory only accounts).
- Accounts MUST NOT be treated as L0 identity or DID.

Authentication Model (MUST)
- Authentication MUST be challenge-based with a server-issued nonce.
- The server MUST store a nonce with a strict TTL and enforce single-use.
- Verification MUST validate the signature against the stored public key.
- The system MUST NOT use passwords, email, phone, OAuth, or personal data.

Session Model (MUST)
- The system MUST issue a short-lived access token or server-side session id.
- Sessions MUST be revocable and have an explicit expiry.
- Session tokens MUST NOT embed secrets in clear text.

Authorization (MUST)
- Chat and faucet endpoints MUST require valid authentication.
- Read-only public endpoints MAY be unauthenticated.

Abuse and Safety (MUST)
- Rate limits MUST apply per IP and per account for sensitive routes.
- Message size MUST be bounded and payload size limits enforced.
- Errors MUST be deterministic and MUST NOT include stack traces or secrets.

Chat Evidence Model (MUST)
- Each message append MUST return a receipt with digest chaining:
  - prev_digest, msg_digest, chain_head.
- msg_digest MUST be hash(canonical_json(message_fields)).
- canonical_json MUST have stable field order and deterministic encoding.
- The receipt chain MUST be stable for the same message sequence.

Change Control
- This document is normative.
- Any change MUST include a version bump and conformance evidence updates.
