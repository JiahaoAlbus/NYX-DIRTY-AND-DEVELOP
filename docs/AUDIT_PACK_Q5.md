# Audit Pack Q5

Purpose
- Provide auditor-ready scope, boundaries, and evidence links for Q5 Router v1 and Reference Client v1.

Scope
- Router v1 package, receipts/replay, conformance drills, and reference client output.

Non-Scope
- Production bridge/on-off ramps.
- Production cryptography or operational deployment.

MUST and MUST NOT
- Audit MUST verify deterministic replay for Router receipts.
- Audit MUST verify no secrets are written to reports or logs.
- Audit MUST verify fee enforcement for state mutations.
- Audit MUST NOT treat client output as authoritative; receipts are authoritative.
- Audit MUST NOT assume any account linkage semantics.

Trust Boundaries
- Core: Router + DEX state transitions and receipts.
- Client: deterministic report shell only; no state authority.
- Conformance: drills are enforcement checks, not runtime logic.

Threat Model Notes
- External tamper attempts against receipts and report data.
- Replay tamper attempts against deterministic state transitions.
- Evidence-format abuse in disclosure/bounty submissions.

Evidence / Verification
- Full verification command set: `docs/AUDIT_REPRO_COMMANDS.md`.
- Router invariants map: `docs/INVARIANT_MAP_DEX_V1.md`.
- Router receipt/replay tests: `packages/l3-router/test`.
- Conformance drills: `packages/conformance-v1/src/conformance_v1/drills.py`.
- Reference client tests: `attic/apps/nyx-reference-client/test`.

Freeze / Change Control
- Router v1 meaning is sealed after Week07; see `docs/DEX_V1_ROUTER_BLUEPRINT.md`.
- Changes follow `docs/CHANGE_CONTROL.md`.

Findings & Mitigations
- 2027-Q1-W11: Added router invalid-swap rejection regression tests (no code change).
