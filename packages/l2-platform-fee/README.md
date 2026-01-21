# l2-platform-fee

Purpose
- Additive platform fee hook layered on top of the protocol fee engine.

Scope
- Provides quote/enforce helpers that preserve protocol fee semantics.
- Uses existing FeeEngineV0 without modification.

Non-Scope
- No changes to protocol fee rules.
- No fee waivers or shortcuts for shared-state mutation.

Rules
- Platform fee MUST be additive and MUST NOT reduce protocol fee to zero.
- Platform fee MAY be zero, but protocol fee requirements still apply.
- Sponsorship may change the payer only; owed amounts remain unchanged.

Verification
- Unit tests under `packages/l2-platform-fee/test`.

Freeze and Change Control
- Changes require versioned updates and regression evidence.
