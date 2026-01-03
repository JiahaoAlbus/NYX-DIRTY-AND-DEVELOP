# NYX_ZK-ID_Spec_v1

Version: v1 (Normative Design Spec)
Scope: Week 3 — 身份的数学边界（不写代码）
Status: Draft (Target: Q1 Freeze)

---

## Normative Language

The key words **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** in this document are to be interpreted as described in RFC 2119.

Each normative requirement is assigned a stable identifier in the form **[NX-§X.Y.Z]**.

An implementation is considered **non-compliant** if it violates **any** requirement labeled **MUST** or **MUST NOT**.

---

## Executive Statement

> **NYX ZK-ID defines the minimum structure required for an identity system to be privacy-preserving by construction.**

This document is intentionally restrictive.

Any system that depends on:
- trusted operators,
- discretionary recovery,
- verifier goodwill,
- or stable identifiers,

is explicitly **out of scope** for NYX ZK-ID.

NYX ZK-ID is not optimized for convenience, growth metrics, or regulatory friendliness.  
It is optimized for **non-linkability under adversarial conditions**.

---

## 0. Goals and Non-Goals

### 0.1 Goals (MUST)

1. **Pseudonymous Verifiability**  
   The system MUST allow subjects to prove claims without revealing identity, secrets, or raw credentials.

2. **Structural Unlinkability**  
   Cross-identity, cross-context, and long-term linkability MUST be treated as first-class attack surfaces and structurally prevented.

3. **Lifecycle-Native Design**  
   Identity generation, usage, rotation, destruction, and recovery MUST each have explicit rules and guarantees.

4. **No Trusted Humans**  
   The protocol MUST NOT rely on administrators, customer support, or discretionary human intervention for identity control.

### 0.2 Non-Goals (Explicitly Out of Scope)

- Enforcing “one-human-one-identity”
- Mandatory real-world identity binding (KYC as a core dependency)
- Protecting users from self-inflicted deanonymization
- Transferable or tradable reputation markets

---

## 1. Core Concepts

### 1.1 Definitions

- **NYX Identity**  
  A protocol-native subject that accumulates permissions and constraints over time.

- **ZK-ID**  
  A zero-knowledge proving interface bound to a NYX Identity, used to assert claims.

- **Wallet**  
  A replaceable key-management interface. A wallet MUST NOT be treated as an identity.

- **Credential**  
  A signed assertion issued by an issuer, usable in zero-knowledge proofs.

- **Claim**  
  A provable statement (e.g. personhood, reputation threshold, eligibility).

- **Context**  
  A domain-separated environment in which proofs are generated and verified.

### 1.2 Abstract Components

- **Root Secret (RS)**: Identity root secret, exclusively controlled by the subject.
- **Context Handle (CH)**: Context-specific derivation material.
- **Proof System**: Any ZK system capable of selective disclosure.
- **Issuer Set**: Entities capable of issuing credentials (not trust anchors).
- **On-chain Anchors**: Commitments, counters, revocation structures, and state markers.

---

## 2. Non-Negotiable Security Invariants (Constitutional)

The following invariants are constitutive. They define the necessary and sufficient conditions for NYX ZK-ID compliance.

Violation of any invariant immediately disqualifies an implementation.

### 2.1 Wallet–Identity Separation

- **[NX-2.1.1]** A wallet, address, account, or keypair **MUST NOT** be used as an identity identifier, root, or proxy.
- **[NX-2.1.2]** Any design that treats a wallet as an identity anchor is **non-compliant by definition**.

### 2.2 Reputation Non-Transferability

- **[NX-2.2.1]** Reputation **MUST** be bound to exactly one NYX Identity.
- **[NX-2.2.2]** Reputation **MUST NOT** be transferred, sold, leased, merged, replayed, or reused across identities.

### 2.3 Unlinkability by Construction

- **[NX-2.3.1]** Proofs generated in different contexts **MUST** be cryptographically unlinkable by default.
- **[NX-2.3.2]** Unlinkability **MUST NOT** rely on user behavior, verifier restraint, or timing assumptions.

### 2.4 Absence of Trusted Intermediaries

- **[NX-2.4.1]** No administrator, operator, issuer, or recovery agent **MAY** possess unilateral authority to alter identity state.

### 2.5 Cost as Immunity

- **[NX-2.5.1]** Any identity action that creates, mutates, or preserves protocol state **MUST** incur a non-zero, protocol-enforced cost.

---

## 3. Identity Lifecycle (Constrained by Invariants)

All lifecycle operations defined in this section are strictly subordinate to the Security Invariants (Section 2) and Hard Prohibitions (Section 5).  
No lifecycle mechanism MAY weaken, bypass, or conditionally suspend those constraints.

### 3.1 Generation

- The Root Secret (RS) MUST be generated locally under exclusive subject control.
- Generation MUST NOT require KYC, real-world identifiers, or platform accounts.
- Generation MUST NOT emit any stable or reusable public identifier.

Any generation mechanism that enables third-party preimage knowledge or identifier reuse is non-compliant.

### 3.2 Usage

- Every proof MUST be bound to a single, explicit context.
- Proof material MUST be domain-separated by context.
- No proof output MAY function as a global identifier.

Verifier convenience MUST NOT be used to justify reduced unlinkability guarantees.

### 3.3 Rotation

Rotation is a mandatory privacy primitive, not an optional hygiene feature.

- Implementations MUST support rotation without identity loss.
- Rotation MUST invalidate all retired material.
- Only explicitly allowed lineage properties MAY persist across rotation.

Any rotation design that enables retrospective cross-context or cross-time linkage is forbidden.

### 3.4 Destruction

- Destroyed identities MUST permanently fail verification.
- Destruction MUST be cryptographically irreversible.
- No privileged override path MAY exist.

### 3.5 Recovery

- Recovery MUST be protocol-defined and non-discretionary.
- No administrator, issuer, or social process MAY unilaterally recover an identity.
- Recovery MUST establish new cryptographic material and explicit lineage.

Recovery mechanisms MUST NOT reintroduce linkability or trusted intermediaries.

---

## 4. Allowed Claims

### 4.1 Personhood

- Claims MAY assert human-ness or non-bot status.
- Real-world identity binding MUST NOT be required.
- Sybil resistance SHOULD rely on cost, credentials, or behavior.

### 4.2 Reputation

- Claims MAY assert thresholds or conditions.
- Exact values SHOULD NOT be disclosed.
- Reputation MUST be identity-bound and non-transferable.

### 4.3 Eligibility

- Compliance-style claims MUST be optional modules.
- Only boolean satisfaction SHOULD be provable.
- No regulatory backdoors are permitted.

---

## 5. Never-Allowed Linkage (Hard Prohibitions)

The following prohibitions are absolute.

Any violation invalidates NYX ZK-ID compliance.

### 5.1 Cross-Identity Linkage

- **[NX-5.1.1]** Distinct NYX Identities controlled by the same entity **MUST NOT** be linkable by default.
- **[NX-5.1.2]** Stable identifiers, secrets, public keys, commitments, or metadata **MUST NOT** be reused across identities.
- **[NX-5.1.3]** Reputation, credit, or historical proofs **MUST NOT** be replayed, bridged, or referenced across identities.

### 5.2 Cross-Context Linkage

- **[NX-5.2.1]** Proof outputs **MUST** be domain-separated by context.
- **[NX-5.2.2]** Nullifiers, tags, or commitments **MUST NOT** be reusable across contexts.
- **[NX-5.2.3]** Verifiers **MUST NOT** be able to correlate proofs from different contexts without explicit subject disclosure.

### 5.3 Cross-Time Linkage

- **[NX-5.3.1]** Long-lived identifiers enabling longitudinal tracking **MUST NOT** exist.
- **[NX-5.3.2]** Rotation **MUST** invalidate all retired materials.

### 5.4 Network and Platform Correlation

- **[NX-5.4.1]** Network-level metadata (IP address, device fingerprint, platform accounts) **MUST** be treated as hostile input.
- **[NX-5.4.2]** The identity layer **MUST NOT** encode, depend on, or expose such metadata.

---

## 6. Identity State Model (Closed World)

The NYX identity state space is closed and finite.

No additional states MAY be introduced without defining a new major version.

States:
- **Active**: Identity may generate proofs and undergo rotation.
- **Rotating**: Transition state with constrained capabilities.
- **Compromised (Optional)**: Defensive state triggering mandatory rotation.
- **Destroyed**: Permanently unusable.
- **Recovered**: Transitional marker pointing to a new Active identity.

State transitions MUST be explicit and verifiable.
Implicit or heuristic-based state inference is forbidden.

---

## 7. Responsibility Boundaries (Locked)

The following boundaries are strict and enforceable.

- **Subject**  
  Controls the Root Secret and initiates lifecycle actions. The subject bears sole responsibility for key hygiene.

- **Issuer**  
  Issues credentials and supports revocation. An issuer MUST NOT control identity state or recovery.

- **Verifier**  
  Verifies proofs. A verifier MUST NOT demand additional identifying material as a verification condition.

- **Protocol**  
  Enforces anchors, costs, and invariants. The protocol MUST NOT expose discretionary or manual override paths.

Any role conflation constitutes non-compliance.

---

## 8. Conceptual Interfaces

- Prove(claim, context, nonce)
- Verify(claim, context, proof)
- Rotate(anchor, proof)
- Destroy(anchor, auth)
- Recover(material, proof)

Any interface requiring wallet address as identity MUST be rejected.

---

## 9. Security Assumptions (Adversarial First)

NYX ZK-ID assumes the following adversaries are always present:

- State-level actors with coercive power
- Platforms capable of metadata surveillance
- Blockchain analytics with full historical access
- External attackers targeting key material
- Internal actors attempting to introduce backdoors

The protocol makes **no assumption of honest behavior** from any external party.

Any feature that relies on goodwill, secrecy, or operational discipline instead of cryptographic or economic constraints is non-compliant.

---

## 10. Open Items (Explicitly Non-Normative)

The following items are intentionally unresolved and MUST NOT be interpreted as implementation discretion to weaken invariants.

- Zero-knowledge proof system selection
- Revocation data structure choice
- Economic parameter calibration
- Reputation encoding strategy

Future specifications MAY extend this document but MUST NOT contradict Sections 2 or 5.

---

## Freeze Boundary

The following sections are considered **constitutionally frozen** for NYX ZK-ID v1:

- Section 2: Non-Negotiable Security Invariants
- Section 5: Never-Allowed Linkage

Any future revision that alters these sections defines a new major version.

---

## Compliance Statement

A system is NYX ZK-ID compliant **if and only if** it satisfies **all** requirements labeled **[NX-2.x]** and **[NX-5.x]**, and implements lifecycle operations in accordance with Section 3.

Any deviation constitutes a distinct, non-compliant identity system, regardless of naming or marketing claims.

