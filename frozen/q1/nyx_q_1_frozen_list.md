# NYX Q1 Frozen List (Week 11)

**Document ID:** NYX_Q1_Frozen_List.md  
**Authoritative Location:** frozen/q1/ (only)
**Note:** Any copies outside frozen/q1 are non-authoritative and must not be used.
**Status:** FROZEN — Q1 2026  
**Freeze Window:** 2026-03-15 → 2026-03-21  
**Authority Level:** Constitutional (v1)

---

## -1. Normative Language (Frozen)

The key words **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** are normative.

- **MUST / MUST NOT** = compliance-critical.
- **SHOULD / SHOULD NOT** = strong default; deviation requires explicit rationale.
- **MAY** = optional.

Interpretation follows RFC 2119 semantics.

---

## -0. Freeze Classification Legend (Frozen)

This freeze uses four classes. Every future change MUST declare which class it touches.

### -0.1 Never Change (Constitutional)
Changing any **Never Change** item defines a **new protocol**, not an upgrade.

### -0.2 Constrained (Monotone-Safe Only)
Changes are allowed only if they **tighten constraints**, **increase auditability**, or **reduce privilege**. Any weakening is invalid.

### -0.3 Policy (Mutable Calibration)
Numeric thresholds, coefficients, durations, and other calibration knobs. Changes are allowed but MUST be explicit, time-delayed, and auditable.

### -0.4 Expandable (Future Surface)
Explicitly deferred design choices that may be decided later **without** weakening any Never Change / Constrained items.

---

## 0. Covered Artifacts (Frozen)

This freeze covers the Q1 normative set.

**Constitutional / Normative Sources**
- NYX Constitution v1 (Draft)
- Threat Model v1
- NYX Not-To-Do List
- NYX_Architecture_v1 (Five-Layer Architecture) — FROZEN
- NYX_ZK-ID_Spec_v1 (Normative)
- NYX_Web2_Gateway_Principles v1 (Normative)
- NYX Economic Rationale v1 (Normative)
- Crypto_Stack_Selection_v1 (Normative)
- Key_Management_Model v1 (Normative)
- Governance_Model_v1 (Design Constraints)
- NYX Whitepaper v1 (Compiled Normative Summary)

**Non-Normative / Audit / Planning (Informative Only)**
- NYX Self-Attack Review (Week 10) — hostile audit (non-binding)
- NYX multi-year schedule — planning (non-binding)

If any conflict exists, higher-authority items prevail per Section 1.

---

---

## 0. Purpose

This document formally freezes all NYX Q1 principles, boundaries, and invariants.

It serves as:
- the **single authoritative checklist** for Q2+ implementation eligibility,
- a **hard rejection filter** for future proposals,
- a **line of no return** for v1 constitutional assumptions.

Anything not explicitly marked as *Expandable* or *Mutable* herein is considered **frozen by default**.

---

## 1. Authority Order (Frozen)

### 1.1 Supremacy Chain (Final)

The following hierarchy is final and MUST NOT be reordered:

The following authority hierarchy is final and MUST NOT be reordered:

1. NYX Constitution v1  
2. Threat Model v1  
3. NYX Not-To-Do List  
4. Architecture v1 (Five-Layer Model)  
5. Subordinate Specs (Identity, Economics, Crypto, Key Mgmt, Governance)

Any artifact conflicting with a higher authority is **invalid by construction**.

### 1.2 Amendment Rule (Frozen)

- Any attempt to change a **Never Change** item MUST be treated as a **new major protocol version**.
- Any attempt to weaken a **Constrained** item is invalid.
- **Policy** changes are permitted only via explicit, time-delayed, auditable governance paths.

### 1.3 Interpretation Default (Frozen)

If a rule is ambiguous, interpretation MUST resolve in favor of:
1) **more restriction**, 2) **more auditability**, 3) **less privilege**.


---

## 2. Constitutionally Frozen (Never Change)

These items define *what NYX is*. Changing any of them defines a **new protocol**, not an upgrade.

### 2.1 Identity & Subject Model
- Identity ≠ human
- Wallet ≠ identity
- No real-world identity binding as a core dependency
- Multiple identities per controller allowed
- Identity is protocol-native and lifecycle-defined

### 2.2 Trust Model
- No trusted administrators
- No discretionary recovery
- No human goodwill assumptions
- No permanent admin keys

### 2.3 Cost & Scarcity
- All shared-state mutations require non-zero fees
- No privileged fee exemptions
- No zero-fee lanes (direct or sponsored)

### 2.4 Privacy & Linkability
- Unlinkability by construction
- Context separation is mandatory
- No stable identifiers across contexts or time
- Network/platform metadata treated as hostile

### 2.5 Web2 Boundary
- Web2 is never a source of truth
- All Web2 access must be mediated by the NYX Gateway
- Gateway MUST NOT bypass anti-abuse or regulatory controls

### 2.6 Governance Supremacy Rules
- Governance is subordinate to Constitution
- Governance cannot touch identity state
- Emergency powers are restrictive-only
- Token ownership ≠ legitimacy

---

## 3. Architecture (Frozen)

### 3.1 Five-Layer Model (Immutable)
- L0: Identity & Cryptography
- L1: Chain / Consensus
- L2: Currency & Settlement
- L3: Markets & Exchange
- L4: Entry Software (Deferred)

### 3.2 Dependency Law (Immutable)
- Strict one-way dependencies only
- No cycles
- No back-propagation of power

### 3.3 Global Invariants
- No free actions
- No trust-based control
- Decentralization over efficiency

---

## 4. Identity System (ZK-ID v1)

### 4.1 Frozen Invariants
- Wallet–Identity separation
- Reputation non-transferability
- Context-bound proofs
- No trusted recovery agents
- Identity lifecycle completeness

### 4.2 Expandable (Future-Safe)
- Proof system selection (within invariant constraints)
- Revocation data structures
- Issuer set size (not authority)

---

## 5. Cryptography Stack

### 5.1 Frozen
- No custom cryptography
- AEAD-only encryption
- Forward secrecy mandatory
- Domain separation everywhere

### 5.2 Expandable
- Post-quantum research track (non-binding)
- ZK curve/prover optimizations

---

## 6. Key Management

### 6.1 Frozen
- Subject-controlled root secrets
- No NYX service can decrypt subject content
- Quorum-controlled release keys
- Mandatory rotation support

### 6.2 Expandable
- Concrete HSM/KMS vendors
- Client-side secure storage implementations

---

## 7. Economics

### 7.1 Frozen
- NYX Token exists as protocol cost unit
- Fees are consensus costs
- No hidden subsidies
- No fee bypass via sponsorship

### 7.2 Constrained (Monotone Only)
- Fee component registry
- Reserve outflow rules

### 7.3 Policy (Mutable)
- Fee coefficients
- Timelock durations
- Spending caps

---

## 8. Governance

### 8.1 Frozen
- Governable scope limited to parameters, upgrades, reserves
- Proposal cost required
- Timelocks mandatory
- No instant execution

### 8.2 Constrained
- Parameter classification (F/C/P)
- Upgrade power-delta declaration

### 8.3 Policy
- Voting mechanics (bounded)
- Proposal thresholds

---

## 9. Explicitly Deferred (Allowed to Change Later)

These are intentionally **not decided** in Q1 and may evolve without violating freeze:

- Chain choice (L1 vs L2 vs Rollup)
- Market mechanism specifics (AMM, auction, hybrid)
- Client/UI product form
- Go-to-market strategy

---

## 10. Explicitly Forbidden Forever

- Treating wallets as identity
- Zero-fee protocol actions
- Silent upgrades
- Privileged backdoors
- Token-as-governance shortcuts
- Web2-as-truth assumptions

---

## 11. Q2 Entry Gate (Go / No-Go)

Q2 implementation work is authorized **if and only if**:

- All items in Sections 2–8 remain unmodified
- Any proposal touching frozen items is rejected automatically
- Any ambiguity is resolved in favor of *more restriction*

---

## 12. Signature

This document marks the end of Q1 design.

From this point forward:
- Design debates stop
- Interpretation narrows
- Code must obey, not reinterpret

**NYX Q1 is hereby frozen.**

### 12.1 Sign-Off (Week 11)

By signing, the signatory acknowledges:
- this freeze is binding,
- any violation is a compliance failure,
- any modification to **Never Change** items implies a new major protocol version.

**Signatories:**

- **Protocol Lead:** Huangjiahao (Founder)  
- **Security Lead:** Huangjiahao (acting)  
- **Governance Lead:** Huangjiahao (acting)

**Freeze Effective Time:** 2026-03-21T23:59:59Z  
**Status:** FROZEN — EFFECTIVE
