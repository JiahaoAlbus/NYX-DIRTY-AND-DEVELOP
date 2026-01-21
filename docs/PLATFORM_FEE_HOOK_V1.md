# Platform Fee Hook v1

Purpose
- Define the additive platform fee hook without changing protocol fee semantics.

Scope
- Applies only to the platform fee hook layer built on top of the protocol fee engine.

Non-Scope
- Does not modify protocol fee rules.
- Does not introduce fee waivers for shared-state mutation.

Definitions
- Protocol fee: the required fee enforced by the protocol fee engine.
- Platform fee: an additive amount charged at an allowed extension point.
- Total due: protocol fee total plus platform fee amount.

Normative Rules
- The platform fee MUST be additive and MUST NOT replace the protocol fee.
- The platform fee MUST NOT reduce the protocol fee to zero.
- The platform fee MAY be zero; protocol fee requirements still apply.
- Sponsorship MUST change payer only; owed amounts MUST remain unchanged.
- The platform fee hook MUST reject mismatched protocol fee vectors.

Security and Abuse Boundaries
- The platform fee hook MUST reject attempts to lower protocol fee amounts.
- The platform fee hook MUST reject unknown or malformed fee inputs.

Evidence and Enforcement
- Unit and property tests MUST confirm additive behavior and payer independence.
- Conformance drills MUST fail if platform fee or protocol fee can be skipped.

Freeze and Change Control
- This specification is normative; changes require a version bump and regression evidence.
