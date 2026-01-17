# DEX v1 Invariant Map

Purpose
- Map each Router v1 invariant to objective evidence.

Scope
- Router action and receipt invariants for v1.

Non-Scope
- Production bridge or on/off ramp behavior.

MUST and MUST NOT
- Evidence MUST be deterministic and reproducible.
- Evidence MUST be tied to a test, drill, or command.

Invariant → Evidence
- Atomic route execution
  - Tests: router atomicity tests (Week04)
  - Replay: router replay tests (Week04)
- Deterministic receipts
  - Tests: golden vectors (Week04)
  - Tests: determinism guards (Week08)
- Integer-only arithmetic
  - Tests: rounding and bounds property tests (Week05)
- Bounds and rejection rules
  - Tests: property tests and guard tests (Week05)
- No account binding semantics
  - Tests: conformance drills (Week08)
- Fee enforcement for mutations
  - Tests: fee bypass drills (Week06)
- Replay tamper rejection
  - Tests: conformance drills (Week08)

Evidence / Verification
- Canonical test command: see docs/AUDIT_REPRO_COMMANDS.md.
- PROPERTY_N is enforced by test output.

Freeze / Change Control
- F0: invariant map is locked after Week02.
- Any invariant change requires a new protocol version.
