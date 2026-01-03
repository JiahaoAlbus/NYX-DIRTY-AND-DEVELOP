# Q2 Implementation Plan (NYX) — v1.0 (Week 12 Deliverable)

**Window:** 2026‑04‑01 → 2026‑06‑30 (Q2 2026)  
**Purpose:** Convert frozen Q1 rules into a **minimal running core** without re‑litigating design.

> Q2 is *implementation*, not ideology.  
> If a task requires changing a frozen invariant, the task is invalid.

---

## 0. Authority & Scope Lock

### 0.1 Authority order (binding)
Q2 work MUST comply with the Q1 Frozen Set and its supremacy chain. Any conflict resolves upward.

### 0.2 What Q2 is allowed to build
Q2 builds **minimum viable execution** of:

- L0: Identity interfaces + lifecycle ops skeleton (ZK‑ID minimal loop)
- L1: Chain/consensus *adapter interface* + a runnable dev environment (environment may be “chosen-by-implementation”, but must not violate invariants)
- L2: Fee enforcement + auditable accounting traces (no free lanes)
- SDK: Wallet *kernel* (no UI) for key mgmt + tx submission + proof plumbing
- Testnet/devnet: “0.1” runnable environment for end‑to‑end smoke tests

### 0.3 What Q2 must not do (explicit)
- UI / growth / user onboarding.
- Token sale narratives, yield programs, price promises.
- Any privileged admin keys for identity, fees, or upgrades.
- Any Gateway behavior that bypasses external anti‑abuse or simulates humans.

---

## 1. Q2 Success Metrics (Go/No‑Go)

Q2 is successful only if all are true:

1. **End‑to‑end demo** exists:
   - generate identity material locally,
   - create a protocol-recognized action that mutates shared state,
   - pay non-zero fees,
   - produce auditable receipts,
   - verify a context-bound claim proof in a test context.

2. **Conformance suite** exists and is enforced in CI:
   - wallet ≠ identity,
   - no free lanes,
   - context separation,
   - no privileged bypass paths.

3. **Release integrity**:
   - pinned dependencies,
   - SBOM for artifacts,
   - signed release candidates.

---

## 2. Deliverables (What We Ship)

### 2.1 Primary deliverables
- **Testnet/Devnet 0.1**: runnable environment with documented setup.
- **Wallet Kernel SDK (no UI)**: key mgmt + tx + proof hooks.
- **Identity prototype**: DID-ish identity object *without* stable identifiers; proof generation/verification API.
- **Fee model MVP**: fee vector + enforcement + accounting trace.

### 2.2 Engineering outputs
- Repo + CI (Week 12 scope, executed as part of Q2 readiness)
- Conformance test suite
- Security baseline (lint, SAST, dependency scanning, fuzz targets)

---

## 3. Workstreams (Epics → Stories)

### Epic A — Repo, CI, Release Integrity
**Goal:** a repo that cannot merge non-compliant code.

**A1. Repository bootstrap**
- Mono-repo structure with layer packages
- Docs/specs mirrored and linked (read-only)

**A2. CI pipeline**
- Build/test/lint/typecheck
- SAST + dependency scan
- SBOM generation
- Conformance suite enforced as a required check

**A3. Release signing (RC only)**
- Signed artifacts
- Verification step in CI

**Acceptance criteria**
- Protected `main` branch; required status checks include conformance + security scans.

---

### Epic B — L0 Identity (ZK‑ID Minimal Loop)
**Goal:** implement the **interfaces and lifecycle state machine** without choosing fancy cryptography prematurely.

**B1. Identity object model (no stable identifier)**
- Local generation of Root Secret
- Context handle derivation (domain-separated)
- No wallet address as identity root/identifier

**B2. Proof envelope (context-bound)**
- `Prove(claim, context, nonce)`
- `Verify(claim, context, proof)`
- Enforce non-replay across contexts (domain separation)

**B3. Lifecycle ops skeleton**
- Rotate / Recover / Destroy operations as state transitions
- Tombstone semantics for Destroy (verification must fail thereafter)

**Acceptance criteria**
- Unit + property tests show:
  - proofs cannot be verified under the wrong context,
  - any context reuse attempt is rejected,
  - rotation invalidates retired material.

---

### Epic C — L2 Economics (Fees + Accounting)
**Goal:** no free actions, no bypasses, auditable money flows.

**C1. Fee component registry (non-parametric)**
- Define component IDs + measurement basis (state/compute/bandwidth/privacy)
- Produce fee vector for an action descriptor

**C2. Fee enforcement**
- Any shared-state mutation requires non-zero fee
- No privileged exemptions (no allowlists)

**C3. Sponsored actions guardrails**
- Sponsorship may change payer, not amount owed
- Fee equivalence tests: sponsored vs non-sponsored must match

**C4. Accounting trace**
- Emit receipts sufficient to reconstruct component breakdown + destination bucket

**Acceptance criteria**
- Conformance tests pass:
  - “Bypass Test” (no state transition with zero fee),
  - “Opacity Test” (fee decomposable),
  - “Hidden Subsidy Test” (no silent reserve drains in MVP).

---

### Epic D — L1 Chain Adapter + Runnable Devnet
**Goal:** a runnable environment that exercises L0/L2 invariants without locking future architecture choices.

**D1. Chain adapter interface**
- `SubmitTx`, `FinalityProof`, `ReadState`, `VerifyStateProof`
- Treat chain signatures as transport/auth only (never identity)

**D2. Devnet/testnet 0.1**
- Deterministic deployment scripts
- Faucet only if it does not create “free lane” semantics (fees still required; faucet is just a funding mechanism)

**Acceptance criteria**
- One command boots a devnet and runs an end-to-end smoke test.

---

### Epic E — Wallet Kernel SDK (No UI)
**Goal:** give developers a clean, safe client core.

**E1. Key management (client-side)**
- Secure storage integration hooks
- No uploading Root Secret / recovery material

**E2. Transaction + fee plumbing**
- Fee quote → pay → submit tx → receipt verification
- Canonical serialization for signed payloads

**E3. Proof plumbing**
- Context-bound proof calls surfaced in SDK, no shortcuts

**Acceptance criteria**
- SDK example:
  - generate identity,
  - obtain fee quote,
  - submit one state-mutating action,
  - verify receipts + proof.

---

## 4. Conformance & Security (Non‑Optional)

### 4.1 Required conformance tests (minimum)
- Wallet ≠ identity (API + data model)
- No free shared-state actions
- No privileged fee bypass
- Proof context separation + non-replay
- No stable identifiers persisted across contexts/time (data model + serialization checks)
- (If Gateway touched) no anti-abuse circumvention, no human simulation

### 4.2 Security gates
- Dependency pinning + lockfile checks
- SAST + secret scanning
- Fuzz targets for parsers/decoders/verification
- SBOM for release artifacts

---

## 5. Risk Register (Q2‑Relevant)

- **Risk: accidental stable identifier** (e.g., reusing commitments/tags)  
  **Mitigation:** property tests + schema review gate.

- **Risk: “helpful” admin toggle sneaks in**  
  **Mitigation:** privileged path lint rule + conformance test.

- **Risk: fee sponsorship becomes a free lane**  
  **Mitigation:** mandatory fee equivalence tests + audit traces.

- **Risk: metadata leakage via logs**  
  **Mitigation:** strict logging policy + CI grep rules for forbidden fields.

---

## 6. Acceptance Checklist (End of Q2)

A Q2 build is shippable if and only if:

- Devnet/testnet 0.1 runs end-to-end demo.
- Conformance suite is required and green.
- No wallet-as-identity patterns exist.
- No shared-state mutation can occur with zero fee.
- Receipts are auditable (fee vector decomposable).
- Release artifacts are reproducible enough for audit and include SBOM + signatures.

---

## References (Binding Sources)
- NYX Q1 Frozen List (Week 11)  
- NYX Constitution v1 (Draft)  
- Threat Model v1  
- NYX Not-To-Do List  
- NYX Architecture v1 (Five-Layer)  
- NYX ZK-ID Spec v1  
- NYX Web2 Gateway Principles v1  
- NYX Economic Rationale v1  
- Crypto Stack Selection v1  
- Key Management Model v1  
- Governance Model v1  
- NYX Whitepaper v1
