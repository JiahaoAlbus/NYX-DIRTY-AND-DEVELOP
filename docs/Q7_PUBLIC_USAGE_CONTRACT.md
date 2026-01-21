# Q7 Public Usage Contract (F1)

Purpose
- Freeze the public output contract for reference UI and evidence export.

Scope
- Applies to evidence outputs emitted by reference UI backends and related CLI wrappers.

Non-Scope
- Does not change protocol semantics or receipt rules.
- Does not define UI visuals or layout.

Definitions
- Evidence payload: the JSON object returned by the evidence endpoint.
- Evidence bundle: the on-disk artifacts exported for audit and replay.

Normative Rules
- The evidence payload MUST include the following fields:
  - protocol_anchor
  - inputs
  - outputs
  - receipt_hashes
  - state_hash
  - replay_ok
  - stdout
- The evidence payload MUST NOT include secret or witness material.
- The evidence payload MUST be deterministic for the same inputs.
- The evidence payload MUST be serialized with stable key ordering.
- The evidence bundle MUST include all required artifacts defined in the evidence format.

Evidence and Enforcement
- Conformance drills MUST fail if any required field is missing.
- Tests MUST validate deterministic outputs for fixed inputs.

Freeze and Change Control
- This contract is F1 frozen at Week 7.
- Changes require a versioned update and regression evidence.
