# Q8 Application Boundaries

Purpose
- Freeze Q8 application boundaries so UI and clients remain thin and non-authoritative.

Scope
- Web portal, backend gateway, and iOS client boundaries.

Non-Scope
- Protocol semantics, receipt rules, fee rules, and identity logic.

Normative Rules
- UI MUST be a thin client that displays evidence verbatim from the backend.
- UI MUST NOT compute or modify evidence fields.
- UI MUST NOT introduce identity, account, wallet, or profile semantics.
- Backend MUST NOT bypass protocol fee enforcement or alter receipt semantics.
- Backend MUST expose deterministic evidence and export artifacts without timestamps.
- iOS client MUST mirror web flows and MUST NOT add new evidence fields.

Evidence and Verification
- Conformance drills MUST fail on missing evidence fields, reordered fields, or bypass attempts.
- Determinism tests MUST confirm identical output for identical inputs.

Freeze and Change Control
- These boundaries are fixed for Q8.
- Any change requires a versioned update and regression evidence.
