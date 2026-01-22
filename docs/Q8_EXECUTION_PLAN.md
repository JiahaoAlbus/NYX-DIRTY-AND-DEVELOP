# Q8 Execution Plan

Purpose
- Define the Q8 execution sequence and deliverables without changing sealed protocol semantics.

Scope
- Q8 Week01–Week13 deliverables for web, backend, iOS, conformance, and operations.
- Evidence-driven execution using the existing evidence contract (Q7).

Non-Scope
- Protocol semantic changes.
- New receipt formats or evidence field changes.
- Any identity, account, or wallet semantics.

Invariants and Rules
- Evidence format v1 fields and ordering MUST remain unchanged.
- Determinism MUST hold for identical inputs across machines.
- Shared-state mutation MUST NOT bypass protocol fees.
- UI and clients MUST display evidence verbatim and MUST NOT compute or modify evidence fields.

Week-by-Week Outline (Titles Only)
- Week01: Q8 kickoff and architecture freeze.
- Week02: Web portal foundation (NYX Web).
- Week03: Backend ecosystem gateway API.
- Week04: Exchange module v1.
- Week05: Chat module v1.
- Week06: Marketplace module v1 + platform fee integration.
- Week07: Entertainment module v1.
- Week08: iOS client v1.
- Week09: Conformance drills for ecosystem actions.
- Week10: Q8 audit pack and reproduction commands.
- Week11: Hardening and deterministic error handling.
- Week12: RC freeze and Go/No-Go preparation.
- Week13: Release window and closeout.

Verification Philosophy
- Use the canonical verification commands defined in Q7 reproducibility docs.
- Evidence and replay correctness MUST be proven by deterministic runs and conformance drills.

Freeze and Change Control
- Q8 does not alter sealed protocol semantics.
- Any change to evidence format or output contract requires a versioned update and regression evidence.
