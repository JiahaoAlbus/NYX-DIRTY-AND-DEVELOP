# NYX Whitepaper v2

**Document ID:** NYX_WHITEPAPER_V2  
**Version:** 2.0.0  
**Status:** Publication Draft (Release-Grade Layout)  
**Last Updated (UTC+8):** 2026-01-19  
**Protocol Anchor (Tag):** `mainnet-1.0`  
**Operator Attestation (Optional Tag):** `mainnet-1.0-attest`  

---

## Legal & Reader Notice

This document is published for technical transparency and auditability.

- **Normative truth** (what the protocol *is*) is defined by the repository’s **Normative Specifications** and the **Machine Semantics** (code) anchored by `mainnet-1.0`.
- This whitepaper is **informative** unless a section explicitly states it is **Normative**.
- In case of conflict, the precedence of truth applies (see Section 1.3).

**No warranties.** This document is provided “as is,” without warranty of any kind.

---

## Document Control

### 0.1 Audience
- Engineers, auditors, reviewers, integrators.

### 0.2 Scope
- Explains the **current** NYX protocol snapshot at `mainnet-1.0`, including determinism, receipts/replay, DEX v0 and Router v1, conformance enforcement, and release gating.

### 0.3 Non-Scope
- User interface products.
- Production bridge deployment.
- Production fiat on/off ramp deployment.
- Ecosystem applications (shopping/chat/entertainment) beyond interface and boundary notes.

### 0.4 Change Control for this Whitepaper
- This whitepaper may be revised without changing protocol semantics.
- Protocol semantics changes are governed by `CHANGE_CONTROL.md` and sealing rules.

---

## Table of Contents

1. Executive Summary
2. Design Goals & Non-Goals
3. Precedence of Truth & Anchor
4. System Model & Layers
5. Core Invariants
6. Determinism Model
7. Receipt / Trace / Replay Contract
8. Fee Engine & Non-Waivable Mutation Fees
9. DEX v0 (L3)
10. Router v1 (Atomic Multi-Step Routing)
11. Conformance as Enforcement
12. Security Case Overview
13. Bridge & On/Off Boundary (Strategy Only)
14. Governance & Change Control
15. Release Readiness & Evidence
16. Ecosystem & Fee Surfaces (Informative)
17. Roadmap (Informative)
18. Verification & Reproducibility
19. Glossary
20. Appendix A — Normative Reference Map
21. Appendix B — Invariant / Evidence Map (Index)
22. Appendix C — Operator Authorization & Attestation

---

# 1. Executive Summary

NYX is a deterministic protocol stack designed around **replayable receipts**, strict **identity separation**, and **non-bypassable fee enforcement** for shared-state mutation. NYX treats “conformance” as a first-class enforcement mechanism: illegal shortcuts (fee bypass, receipt tampering, replay mutation, account/identity leakage) are encoded as drills whose failure is a merge-blocking condition.

At the `mainnet-1.0` anchor, NYX ships:

- A sealed baseline for earlier phases (Q1–Q3) and a sealed DEX core (DEX v0) with actions: **CreatePool**, **AddLiquidity**, **RemoveLiquidity**, **Swap**.
- A Router v1 enabling **atomic multi-step routing** with fee binding and deterministic replay.
- Deterministic receipts and replay contracts with guards, golden vectors, property invariants (PROPERTY_N), and bounded exploration within strict bounds.
- Audit-grade evidence templates and Go/No-Go gating supporting release truthfulness.

NYX deliberately defers UI and production bridging/on-off ramps to keep core semantics sealed and auditable.

---

# 2. Design Goals & Non-Goals

## 2.1 Goals

NYX aims to provide:

1. **Deterministic execution**
   - No system time dependence.
   - Integer-only critical math.
   - Stable, canonical serialization.

2. **Receipt-based replay**
   - Every shared-state transition yields receipts sufficient to replay deterministically.
   - Replay correctness is testable, enforceable, and portable.

3. **Identity separation**
   - identity ≠ wallet ≠ account.
   - Sender/signature has no identity semantics.

4. **Non-waivable shared-state fees**
   - shared-state mutation ⇒ fee_total > 0.
   - Sponsor may change payer only; fee amount never waived.

5. **Conformance as enforcement**
   - Encode forbidden behaviors as deterministic drills.
   - Failures block merges.

6. **Sealed baselines**
   - Semantics freeze with strict change control; patch-only post-freeze unless additive extensions.

## 2.2 Non-Goals

NYX does not aim to:

- Provide a production-ready bridge or on/off ramp inside the core protocol.
- Introduce privileged admin controls, allowlists, or backdoors.
- Bind economic ownership (LP, balances) to identity/account semantics.
- Offer a consumer UI as part of the core protocol release.

---

# 3. Precedence of Truth & Anchor

## 3.1 Anchor

The executable protocol snapshot is anchored by:

- **Protocol Tag:** `mainnet-1.0`

Optional human authorization may be recorded as an annotated tag, e.g.:

- **Operator Attestation Tag:** `mainnet-1.0-attest`

## 3.2 Snapshot Philosophy

The anchor is a **fixed commit**. Auditors and integrators should treat the anchored commit as the ground truth for:

- code semantics
- normative documents
- evidence commands

## 3.3 Precedence of Truth

1. **Machine Semantics at the anchor** (deterministic transitions, receipts, replay)
2. **Normative Spec documents** (MUST/MUST NOT, invariants, boundaries)
3. **Operational documents** (runbooks, checklists, evidence reports)
4. **This whitepaper** (informative)

---

# 4. System Model & Layers

NYX follows a layered model with one-way dependencies.

## 4.1 Layers

- **L0 — Identity & Cryptographic Boundaries**
  - Context separation rules
  - Witness/secret non-leak rules
  - Identity is not personhood

- **L1 — Chain Adapter (Non-production boundary)**
  - Deterministic adapter interfaces
  - Replayable trace framing

- **L2 — Economics / Fee Engine**
  - Non-waivable mutation fees
  - Sponsor equivalence and payer substitution only

- **L3 — Market / DEX & Router**
  - DEX v0 state/actions/receipts/replay
  - Router v1 atomic routing with fee binding

- **L4 — Entrance Software / Applications (Deferred)**
  - UI, wallets, marketplaces, social/chat, entertainment
  - Built additively without changing sealed core

## 4.2 Trust Boundaries (High-level)

- **Core** (anchored semantics): MUST NOT trust UI, bridges, or off-chain services.
- **Adapters** (bridge/on-off): maximum attack surface; treated as untrusted.
- **Operators**: may produce attestations, but cannot override protocol rules.

---

# 5. Core Invariants

NYX core invariants are non-negotiable and must be enforceable.

## 5.1 Identity Separation

- identity ≠ wallet ≠ account.
- Sender/signature has no identity semantics.
- Same payload, different sender ⇒ same meaning.

## 5.2 Non-Waivable Fees for Shared-State Mutation

- Any shared-state mutation MUST satisfy fee_total > 0.
- Sponsor MAY change payer only; fee amount MUST NOT be waived.

## 5.3 Context Separation

- Proofs MUST be bound to a context and statement.
- Wrong context/statement MUST fail.

## 5.4 Determinism & Replayability

- Receipts MUST be sufficient for deterministic replay.
- Serialization MUST be stable.
- Replay MUST recreate the exact final state.

## 5.5 No Secret Leakage

- Root secrets/witnesses MUST NOT appear in logs, receipts, traces.

## 5.6 No Backdoors

- No allowlists, admin overrides, or privileged bypass pathways.

---

# 6. Determinism Model

NYX adopts a strict determinism policy for machine semantics.

## 6.1 Prohibitions

- No `time()` dependence.
- No reliance on environment variables for semantics.
- No non-seeded randomness in core logic.

## 6.2 Numeric Rules

- Integer arithmetic only for critical protocol math.
- Rounding rules MUST be explicit and tested.
- Inputs MUST be bounded and validated.

## 6.3 Determinism Guards

Determinism is enforced via:

- golden vectors
- replay verification tests
- determinism guard tests
- conformance drills that detect nondeterministic outputs

---

# 7. Receipt / Trace / Replay Contract

## 7.1 Receipt Requirements

Receipts MUST:

- be sufficient to replay deterministically
- contain no secrets
- use canonical ordering and stable serialization
- produce stable receipt hashes

## 7.2 Replay Requirements

Replay MUST:

- accept (prior state, receipt) and yield the exact next state
- reject tampered receipts
- produce identical state hashes across machines

## 7.3 Evidence

Replay correctness is verified through:

- unit tests for replay
- golden vectors
- end-to-end deterministic demos
- conformance drills (tamper/replay-mutate)

---

# 8. Fee Engine & Non-Waivable Mutation Fees

## 8.1 Structural Enforcement

Fee enforcement must be structural (hard to bypass), not optional.

## 8.2 Sponsor Equivalence

- Sponsor may substitute payer.
- Fee amount is invariant under payer substitution.

## 8.3 Evidence

- unit tests for non-zero fee
- property tests for payer independence
- conformance drills for bypass attempts

---

# 9. DEX v0 (L3)

## 9.1 Overview

DEX v0 provides a minimal AMM core:

- CreatePool
- AddLiquidity
- RemoveLiquidity
- Swap

DEX v0 is intentionally narrow to maximize auditability and prevent semantic sprawl.

## 9.2 State Model

A pool maintains integer reserves and LP supply.

- reserves are non-negative integers
- LP supply is a non-negative integer
- rounding rules are explicit

## 9.3 Actions

### CreatePool
- creates a pool with deterministic initial state

### AddLiquidity
- adds reserves and mints LP under deterministic rules

### RemoveLiquidity
- burns LP and returns reserves under deterministic rules
- enforces exit-right invariant

### Swap
- constant-product style swap under integer math
- applies swap fee as specified
- rejects invalid inputs and pathological values

## 9.4 Receipts and Replay

- Each action produces a deterministic receipt.
- Receipts are replayable into identical final state.

## 9.5 Invariants & Testing

DEX invariants are enforced by:

- property tests (PROPERTY_N)
- bounded explorer (strict small bounds)
- golden vectors
- determinism guards
- conformance drills

---

# 10. Router v1 (Atomic Multi-Step Routing)

## 10.1 Motivation

Router v1 enables deterministic, atomic routes composed of multiple steps.

## 10.2 Atomicity

- A route is all-or-nothing.
- Partial application MUST NOT occur.

## 10.3 Fee Binding

- Route execution binds to fee enforcement.
- Sponsor equivalence is maintained.

## 10.4 Receipts & Replay

- Router receipts include ordered step receipts.
- Replay reproduces identical final state hash.

---

# 11. Conformance as Enforcement

NYX treats conformance as the enforcement layer for sealed rules.

## 11.1 “CI Death Penalty” Principle

If conformance drills detect:

- fee bypass
- receipt tampering
- replay mutation
- identity/account leakage via sender semantics
- nondeterministic serialization

Then the change MUST NOT be merged.

## 11.2 What Conformance Guards

- invariants in frozen rules
- determinism contracts
- anti-backdoor posture

---

# 12. Security Case Overview

NYX’s security case is organized as claims + evidence.

## 12.1 Claims (Examples)

- C1: Shared-state mutation cannot be performed without a non-zero fee.
- C2: Receipt replay reproduces identical final state.
- C3: Wrong context/statement proofs fail deterministically.
- C4: Secrets are not leaked through receipts/traces.

## 12.2 Evidence

Evidence is provided by:

- invariant maps
- tests and property suites
- bounded explorer
- conformance drills
- audit pack and repro commands

---

# 13. Bridge & On/Off Boundary (Strategy Only)

NYX does not ship production bridging/on-off in core.

## 13.1 Requirements

- Core MUST NOT trust adapters.
- Adapters are treated as maximum attack surface.

## 13.2 What is Frozen

- adapter interface boundaries
- evidence formats
- threat model expectations
- conformance drills preventing privileged assumptions

---

# 14. Governance & Change Control

NYX enforces a sealed baseline doctrine.

## 14.1 Sealed Baselines

- Q1–Q3 deliverables are SEALED.
- DEX v0 and Router v1 semantics are SEALED after freeze.

## 14.2 Allowed Changes Post-Freeze

- Patch bugfixes with **zero semantic change** AND mandatory regression tests/drills
- Additive extensions that do not alter sealed semantics

Any semantic change requires a new version/deployment boundary.

---

# 15. Release Readiness & Evidence

NYX uses objective Go/No-Go criteria.

## 15.1 Go/No-Go Criteria (Illustrative)

- full test suite green
- property tests green at PROPERTY_N
- bounded explorer green
- conformance drills green
- determinism guards green
- audit pack complete
- runbooks complete
- key ceremony evidence complete
- OPSEC model complete

## 15.2 Attestation

A release MAY be accompanied by a human operator attestation tag.

---

# 16. Ecosystem & Fee Surfaces (Informative)

NYX can support multiple fee surfaces without changing sealed semantics:

- protocol fees (mutation fees)
- market fees (swap fees)
- platform fees (applications at L4)

Ecosystem applications (shopping/chat/entertainment) are expected to live above core semantics.

---

# 17. Roadmap (Informative)

A conservative, additive roadmap includes:

- L4 reference UI (non-normative)
- ecosystem modules built as additive layers
- optional advanced DEX features as **new versioned modules** (not semantic changes)

---

# 18. Verification & Reproducibility

## 18.1 Checkout Anchor

- `git fetch --tags`
- `git checkout -f mainnet-1.0`

## 18.2 Canonical Verification

Use the repository’s documented canonical commands (audit repro commands).

## 18.3 Deterministic Demos

Run deterministic demos and verify:

- stable state_hash
- stable receipt hashes
- replay_ok == True

---

# 19. Glossary

- **Normative:** defines MUST/MUST NOT protocol rules.
- **Informative:** explanatory; not protocol truth.
- **Receipt:** deterministic transition record sufficient to replay.
- **Replay:** deterministic reconstruction from receipt chain.
- **Conformance:** enforcement suite rejecting illegal shortcuts.
- **Frozen/Sealed:** semantics are locked; only patch-only or additive changes allowed.

---

# 20. Appendix A — Normative Reference Map

The following repository documents are typically treated as normative at the anchor:

- DEX blueprint and router blueprint
- invariant maps
- security case
- change control and sealing rules
- immutable rules indices

See the repository’s artifact index for path-level classification.

---

# 21. Appendix B — Invariant / Evidence Map (Index)

Invariants are mapped to:

- property tests (PROPERTY_N)
- bounded explorer
- golden vectors
- determinism guards
- conformance drills

See the repository invariant maps for exact file-level evidence pointers.

---

# 22. Appendix C — Operator Authorization & Attestation

This section describes an optional human authorization workflow.

## 22.1 Recommended Attestation Pattern

- Create an annotated tag referencing the mainnet tag commit.
- The message should include the operator name and explicit authorization.

Example:

> "I, <OperatorName>, authorize NYX mainnet-1.0."

This attestation MUST NOT change protocol semantics.

