## Purpose
- Define the Testnet Beta chat module boundaries, receipts, and evidence requirements.

## Scope
- Message envelopes written to the testnet storage layer.
- Deterministic receipts and evidence exports for send actions.
- Client expectations for evidence display and replay checks.

## Non-Scope
- No real-time network claims or global live messaging service.
- No user profiles, no external account linkage, no social graph.
- No moderation, abuse detection, or content ranking features.

## Definitions
- "Message envelope": deterministic payload containing channel, body, and sender address.
- "Receipt": deterministic result produced by the backend for a send action.
- "Evidence bundle": the required export set defined by the Q7 evidence format.

## Normative Rules (MUST / MUST NOT)
- The chat module MUST treat message send as a deterministic action.
- The chat module MUST produce a receipt and evidence bundle for each send action.
- The chat module MUST export evidence fields verbatim and in the required order.
- The chat module MUST keep evidence deterministic for the same recorded inputs.
- The chat module MUST NOT claim live global presence, live network status, or mainnet activity.
- The chat module MUST NOT store or display user profiles or balance information.
- The chat module MUST NOT embed secrets, seeds, or private keys in logs or evidence artifacts.
- The chat module MUST use explicit seed and run_id inputs for deterministic runs.

## Security and Abuse Boundaries
- Payloads MUST be size-bounded and validated.
- Rate limiting MUST be applied at the backend gateway.
- Error messages MUST be deterministic and MUST NOT expose sensitive inputs.

## Evidence and Verification
- Evidence fields required:
  - protocol_anchor, inputs, outputs, receipt_hashes, state_hash, replay_ok, stdout
- The evidence bundle MUST be exportable as a deterministic zip with fixed metadata.
- Replay validation MUST return replay_ok=True for valid evidence.

## Freeze and Change Control
- This specification is normative for Q10 Testnet Beta.
- Any change MUST be additive and MUST NOT alter existing evidence outputs.
