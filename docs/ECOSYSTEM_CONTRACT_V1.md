# Ecosystem Contract v1

## Purpose
Define the normative rules for ecosystem components that integrate with the sealed NYX protocol.

## Scope
This contract applies to:
- UI shells and reference clients.
- SDK wrappers that expose protocol calls.
- Adapter services that collect evidence or route requests.
- Extension services that consume receipts or traces.

## Non-Scope
- Protocol changes or new protocol semantics.
- Fee rule changes or fee waivers.
- Any cryptographic implementation changes.

## Definitions
- Protocol core: sealed protocol logic and invariants implemented in packages/.
- Extension point: a documented integration boundary outside protocol core.
- Platform fee: an additive fee charged by an extension at a defined boundary.
- Evidence artifact: receipt, trace, or report used for replay and audit.
- Receipt: deterministic record sufficient for replay verification.
- Trace: deterministic sequence of receipts with stable hashing.

## Normative Rules (MUST/MUST NOT)
- Implementations MUST treat protocol core semantics as sealed and immutable for Q6.
- Implementations MUST NOT introduce new protocol semantics through client logic.
- Implementations MUST NOT treat sender or account identifiers as identity.
- Implementations MUST NOT embed secrets in logs, receipts, traces, or error strings.
- Implementations MUST use deterministic inputs and outputs for evidence artifacts.
- Implementations MUST keep fee evidence complete and replayable.
- Implementations MUST NOT provide any fee waiver or skip path for shared-state mutation.
- Implementations MUST NOT add alternate execution paths that bypass receipt replay.

## Security and Abuse Boundaries
- Adapters are untrusted and MUST NOT be granted special trust in protocol validation.
- Evidence artifacts MUST be sufficient to detect tampering and replay errors.
- Any extension that cannot produce replayable evidence MUST be treated as non-compliant.

## Evidence and Enforcement
- Conformance drills MUST reject any path that skips protocol fee enforcement.
- Deterministic demos MUST produce stable receipt hashes for audit.
- Property tests MUST cover invariants referenced by this contract.

## Change Control
This contract is normative. Changes require an explicit version bump and evidence that sealed invariants remain unchanged.
