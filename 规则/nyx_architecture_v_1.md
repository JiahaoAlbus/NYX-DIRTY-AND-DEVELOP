# NYX_Architecture_v1 — Five-Layer Architecture Specification (Frozen)

**Document ID**: NYX_Architecture_v1.md  
**Version**: 1.0.0 (Architecture Freeze)  
**Status**: FROZEN (Week 8)  
**Last Updated**: 2026-01-03  

> This document is a **normative** architecture specification for NYX.
> It defines the five-layer model, strict one-way dependencies, cross-layer contracts, and global invariants.
> It intentionally avoids implementation detail.

---

## 0. Governance of This Document

### 0.1 Authority Order

This document is subordinate to:

1. NYX Constitution v1 (Draft)
2. Threat Model v1
3. NYX Not-To-Do List

If any conflict exists, higher-authority documents prevail.

This document is aligned with (non-authoritative for conflicts):
- NYX ZK-ID Specification v1
- NYX Web2 Gateway Principles
- NYX Economic Rationale

### 0.2 Normative Language

The key words **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** are to be interpreted as described in RFC 2119 and clarified by RFC 8174 (capitalization requirement).

All normative requirements are labeled **[NX-ARCH-§X.Y.Z]**.

### 0.3 Terminology (Normative)

- **Layer**: A responsibility-bounded module with explicit contracts and one-way dependencies.
- **Dependency**: A required reliance on another layer’s guarantees for correctness.
- **Correctness**: The property that protocol rules can be verified without discretionary human intervention.
- **Shared-state mutation**: Any action that changes protocol state visible to more than one participant.
- **Privileged path**: Any mechanism that provides an inclusion, fee, execution, or identity advantage not available under the same public rules.

- **[NX-ARCH-§0.3.1]** Terms in this section are normative for this document.

### 0.4 Document Change Control

- **[NX-ARCH-§0.4.1]** Changes to frozen sections require a new **major** version (e.g., 2.0.0) and MUST include an explicit rationale and threat-model impact assessment.
- **[NX-ARCH-§0.4.2]** **Minor** versions (e.g., 1.1.0) MAY add non-normative appendices or clarifications that do not alter any MUST/MUST NOT requirement.
- **[NX-ARCH-§0.4.3]** **Patch** versions (e.g., 1.0.1) MUST be editorial only (typos, formatting, references) with zero semantic change.

### 0.5 Freeze Boundary

The following sections are **frozen** for Architecture v1 and MUST NOT be modified without a new major version:

- Section 1: Layer definitions (L0–L4)
- Section 2: One-way dependency law
- Section 3: Cross-layer contracts (interfaces + invariants)
- Section 4: Global invariants
- Section 5: Boundary rules and forbidden patterns

Non-normative appendices MAY change without violating the freeze.

---

## 1. Architecture Overview

NYX is a protocol-centered digital order whose security, legitimacy, and capture-resistance are enforced by **structure**, not trust.

NYX is frozen as a **five-layer stack** with **strictly one-way dependencies**.

The architecture is designed so that:
- core correctness does not depend on discretionary human intervention,
- identities remain unlinkable by default,
- state mutations are never free,
- markets cannot introduce privileged lanes,
- Web2 integration cannot back-propagate power into core layers.

---

## 2. Five-Layer Model (L0–L4)

| Layer | Name | Primary Responsibility | Outputs (Conceptual) |
|---:|---|---|---|
| L0 | Identity & Cryptography | Subjects, proofs, key lifecycle, unlinkability | proofs, commitments, encryption/auth primitives |
| L1 | Chain / Consensus | Ordering, availability, deterministic state machine, finality | blocks, state roots, inclusion/finality proofs |
| L2 | Currency & Settlement | Protocol cost unit, fees, accounting, settlement finality | fee rules, fee receipts, settlement receipts |
| L3 | Markets & Exchange | Market primitives, routing/execution policies, anti-capture design | quotes, execution receipts, market state views |
| L4 | Entry Software (Deferred) | Client/gateway software, Web2 integration surfaces | user agents, gateways, distribution/ops wrappers |

### 2.1 Layer Responsibility Boundaries

- **[NX-ARCH-§2.1.1]** L0 defines identity and cryptographic correctness; it MUST NOT rely on chain state or Web2 metadata as truth.
- **[NX-ARCH-§2.1.2]** L1 defines shared state correctness; it MUST NOT depend on economics or market outcomes for correctness.
- **[NX-ARCH-§2.1.3]** L2 defines cost and settlement; it MUST NOT depend on market mechanisms for fee enforcement.
- **[NX-ARCH-§2.1.4]** L3 defines markets; it MUST NOT introduce privileged orderflow lanes.
- **[NX-ARCH-§2.1.5]** L4 is integration-only; it MUST NOT redefine L0–L3 invariants.

### 2.2 L4 Deferred Constraint

- **[NX-ARCH-§2.2.1]** L4 is explicitly deferred and MUST NOT be required for validating correctness of L0–L3.
- **[NX-ARCH-§2.2.2]** Any future L4 MUST comply with NYX Web2 Gateway Principles and MUST NOT create stable identifiers or privileged access paths.

---

## 3. One-Way Dependency Law

### 3.1 Core Rule

- **[NX-ARCH-§3.1.1]** Dependencies MUST flow strictly upward: a layer may depend only on lower layers.
- **[NX-ARCH-§3.1.2]** No layer may import policy, truth, or required state from any higher layer.
- **[NX-ARCH-§3.1.3]** Cycles and bidirectional dependencies are forbidden.
- **[NX-ARCH-§3.1.4]** Cross-layer access MUST occur only through explicitly defined interfaces.

### 3.2 Allowed Dependency Graph

```
L4  Entry Software (Deferred)
 ↑
L3  Markets & Exchange
 ↑
L2  Currency & Settlement
 ↑
L1  Chain / Consensus
 ↑
L0  Identity & Cryptography
```

Allowed edges:
- L1 → L0
- L2 → L1, L0
- L3 → L2, L1, L0
- L4 → L3, L2, L1, L0

---

## 4. Cross-Layer Contracts (Interfaces + Invariants)

This section defines the only permitted ways layers may consume lower-layer functionality.

### 4.1 L0 → L1–L4: Identity & Proof Surfaces

**Conceptual Interfaces** (names are illustrative, not implementation-binding):
- `Prove(claim, context, nonce) -> proof`
- `Verify(claim, context, proof) -> bool`
- `Rotate(authorization) -> new_key_material`
- `Recover(recovery_proof) -> new_key_material`
- `Destroy(authorization) -> tombstone`

**Invariants**
- **[NX-ARCH-§4.1.1]** Identity MUST be independent of wallets, addresses, or accounts.
- **[NX-ARCH-§4.1.2]** Proofs MUST be domain-separated by context and unlinkable by default.
- **[NX-ARCH-§4.1.3]** Network/platform identifiers MUST be treated as hostile input and MUST NOT become identity state.

### 4.2 L1 → L2–L4: State, Ordering, Finality

**Conceptual Interfaces**
- `SubmitTx(tx) -> inclusion_receipt`
- `FinalityProof(ref) -> finality_evidence`
- `ReadState(path) -> value`
- `VerifyStateProof(path, proof) -> bool`

**Invariants**
- **[NX-ARCH-§4.2.1]** L1 MUST provide deterministic state transitions and verifiable state proofs.
- **[NX-ARCH-§4.2.2]** L1 MUST NOT rely on privileged roles or discretionary override paths.

### 4.3 L2 → L3–L4: Cost, Fees, Settlement

**Conceptual Interfaces**
- `FeeQuote(action_descriptor) -> fee_vector`
- `PayFee(fee_vector, payer_context) -> fee_receipt`
- `Settle(asset, amount, to, context) -> settlement_receipt`
- `AccountingTrace(ref) -> {components, destinations}`

**Invariants**
- **[NX-ARCH-§4.3.1]** Any shared-state mutation MUST incur a non-zero protocol-enforced cost.
- **[NX-ARCH-§4.3.2]** Fee bypasses or discretionary exemptions are forbidden.
- **[NX-ARCH-§4.3.3]** Accounting flows MUST be auditable.

### 4.4 L3 → L4: Market Primitives Without Capture

**Conceptual Interfaces**
- `Quote(pair, size, constraints) -> quote`
- `Route(order) -> execution_plan`
- `Execute(order, context) -> trade_receipt`
- `PublishMarketState(snapshot_ref) -> view`

**Invariants**
- **[NX-ARCH-§4.4.1]** L3 MUST NOT introduce privileged orderflow lanes or private execution advantages.
- **[NX-ARCH-§4.4.2]** Market mechanisms MUST treat capture/MEV as first-class attack surfaces.

---

## 5. Boundary Rules and Forbidden Patterns

### 5.1 Forbidden Dependency Examples

- **[NX-ARCH-§5.1.1]** L0 MUST NOT depend on L1/L2/L3/L4 for truth or correctness.
- **[NX-ARCH-§5.1.2]** L1 MUST NOT depend on L2 for consensus correctness.
- **[NX-ARCH-§5.1.3]** L2 MUST NOT depend on L3 market outcomes to enforce fees or settlement.
- **[NX-ARCH-§5.1.4]** L3 MUST NOT depend on L4 UX/client logic for correctness.

### 5.2 Forbidden “Back-Propagation”

- **[NX-ARCH-§5.2.1]** No higher layer may introduce a requirement that forces changes to a lower-layer invariant.
- **[NX-ARCH-§5.2.2]** Web2-derived rules MUST NOT be treated as protocol rules.

### 5.3 No Hidden Side-Channels

- **[NX-ARCH-§5.3.1]** Any cross-layer data flow MUST be explicit and auditable.
- **[NX-ARCH-§5.3.2]** Stable identifiers across contexts are forbidden unless explicitly specified by L0 and justified by the threat model.

---

## 6. Global Architectural Invariants

### 6.1 No Trust-Based Control

- **[NX-ARCH-§6.1.1]** Core security and identity control MUST NOT depend on discretionary human intervention.

### 6.2 No Free Actions

- **[NX-ARCH-§6.2.1]** There MUST be no free protocol-level shared-state actions.

### 6.3 Web2 as Hostile Input

- **[NX-ARCH-§6.3.1]** Web2 systems MUST NOT be treated as sources of truth.

### 6.4 Decentralization Over Efficiency

- **[NX-ARCH-§6.4.1]** Any optimization that weakens decentralization or introduces irreversible power concentration is invalid.

---

## 7. Freeze Acceptance Criteria (Go/No-Go)

Architecture v1 is considered correctly frozen if and only if all items below are true:

- **[NX-ARCH-§7.1.1]** Layers L0–L4 are defined with non-overlapping responsibilities.
- **[NX-ARCH-§7.1.2]** The dependency graph is strictly one-way and has no cycles.
- **[NX-ARCH-§7.1.3]** Cross-layer consumption occurs only via Section 4 contracts.
- **[NX-ARCH-§7.1.4]** Global invariants in Section 6 are not weakened by any layer.
- **[NX-ARCH-§7.1.5]** L4 remains optional for L0–L3 correctness.

---

## Appendix A (Non-Normative): Open Implementation Choices

The following are intentionally not frozen here and MUST NOT be used to weaken any frozen invariant:
- execution form factor (rollup, appchain, etc.)
- proof system selection
- market mechanism specifics (AMM, auction, hybrid)
- gateway product form factor

---

*End of NYX_Architecture_v1*

