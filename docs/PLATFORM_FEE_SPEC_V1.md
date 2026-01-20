# Platform Fee Specification v1

## Purpose
Define additive platform-fee rules for ecosystem extensions without changing protocol fee semantics.

## Scope
This specification applies to any extension or client that charges an additional fee outside protocol core.

## Non-Scope
- Protocol fee calculations or fee engine rules.
- Any changes to protocol invariants or state transition logic.
- Any off-chain settlement or payment method selection.

## Definitions
- Protocol fee: the non-waivable fee enforced by the protocol fee engine.
- Platform fee: an additive fee collected by an extension at a defined boundary.
- Shared-state mutation: any action that changes protocol state.
- Extension point: a documented boundary outside protocol core where additive fees may be collected.

## Normative Rules (MUST/MUST NOT)
- Platform fee MUST NOT replace protocol fee.
- Platform fee MAY be additive (overlay) or collected at explicitly defined extension points only.
- No pathway may bypass non-waivable protocol fees for shared-state mutation.
- Platform fee MUST be expressed with integer-only amounts and deterministic rounding.
- Platform fee MUST NOT depend on sender or account identifiers.
- Platform fee evidence MUST be recorded in receipts or traces when applicable.
- Platform fee collection MUST NOT alter protocol fee enforcement outcomes.

## Security and Abuse Boundaries
- Extensions MUST NOT create a fee waiver path for protocol mutations.
- Extensions MUST NOT claim protocol compliance without replayable evidence.
- Extensions MUST provide evidence artifacts that allow deterministic verification.

## Evidence and Enforcement
- Conformance drills SHOULD test additive-fee integrity and rejection of fee waivers.
- Determinism guards SHOULD verify stable fee evidence across runs.

## Change Control
This specification is normative. Changes require a version bump and documented evidence of no protocol semantic drift.
