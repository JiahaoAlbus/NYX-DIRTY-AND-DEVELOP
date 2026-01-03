# NYX Economic Rationale (v1 — Executive-Grade)

> **Scope (Week 6)**: Economic legitimacy of NYX (NOT a token launch plan).
>
> **This document explains**: why NYX Token must exist, why fees are structurally required, and how value flows back into protocol sustainability.
>
> **This document explicitly excludes**: issuance schedules, sales, “tokenomics marketing,” APY programs, price targets, speculative narratives, or user-growth subsidies.

---

## Normative Language

The key words **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** in this document are to be interpreted as described in RFC 2119.

Each normative requirement is assigned an identifier in the form **[NX-EC-§X.Y.Z]**.

---

## Table of Contents

- [Normative Language](#normative-language)
- [Terminology and Model Primitives](#terminology-and-model-primitives)
- [0. Authority and Alignment](#0-authority-and-alignment)
- [1. Executive Statement](#1-executive-statement)
- [2. Design Objectives](#2-design-objectives-what-legitimate-economics-means)
- [3. Why NYX Token Must Exist](#3-why-nyx-token-must-exist)
- [4. Why Fees Are Structurally Required](#4-why-fees-are-structurally-required)
- [5. What Fees Price](#5-what-fees-price-principles-only-no-parameters)
- [6. Value Return](#6-value-return-how-fees-flow-back-into-system-sustainability)
- [7. Governance Safety](#7-governance-safety-economic-power--political-power)
- [8. Adversarial Review](#8-adversarial-review-if-i-wanted-to-break-nyx-economics)
- [9. Economic Health Invariants](#9-economic-health-invariants-operationally-testable)
- [10. Hard Requirements](#10-hard-requirements-non-negotiable)
- [11. Open Items](#11-open-items-intentionally-out-of-scope)
- [12. Freeze Boundary](#12-freeze-boundary-v1)
- [13. Summary](#13-summary)
- [Appendix A — Economic Change Control](#appendix-a--economic-change-control)
- [Appendix B — Fee Sponsorship & Meta-Transaction Guardrails](#appendix-b--fee-sponsorship--meta-transaction-guardrails)
- [Appendix C — Service Receipt Schema](#appendix-c--service-receipt-schema)
- [Appendix D — Privacy Parity Invariant](#appendix-d--privacy-parity-invariant)
- [Appendix E — MEV & Orderflow Capture Policy](#appendix-e--mev--orderflow-capture-policy)
- [Appendix F — Economic Telemetry Spec](#appendix-f--economic-telemetry-spec)
- [Appendix G — Cross-Document Integration Points](#appendix-g--cross-document-integration-points)
- [Appendix H — Changelog](#appendix-h--changelog)

---

## Terminology and Model Primitives

This section defines the minimum economic vocabulary used in NYX. These definitions are **normative** for this document.

- **Action**: a protocol-recognized operation that consumes shared resources or changes shared state.
- **Shared Resource**: any scarce capability whose consumption imposes cost on other participants (bandwidth, compute, state, privacy mediation).
- **State Transition**: any action that creates, mutates, preserves, or deletes protocol-relevant state.
- **Fee Vector**: an additive set of fee components priced against objective scarcity surfaces, rather than a single opaque fee.
- **Fee Component**: an individually explainable cost term tied to a measurable scarcity surface (e.g., State Write Fee, Verify Fee).
- **Subsidy**: any mechanism where a payer differs from the consumer of a resource. Subsidies are **allowed only if explicit, auditable, and non-discretionary**.
- **Reserve**: a protocol-controlled buffer used to fund security-critical work and absorb adversarial shocks under rule-governed constraints.
- **Emergency Mode**: a strictly restrictive state that can only *remove capabilities* (pause/slow/raise-cost), never grant new privileges.

### Economic Legitimacy Criterion

NYX economics is legitimate if and only if:

1. Scarcity is priced by objective rules.
2. Costs are internalized and non-bypassable.
3. Security and critical operations are fundable without discretionary fundraising.
4. Economic power does not automatically translate into unconstrained governance power.

---

## 0. Authority and Alignment

This document is **subordinate** to:

- **NYX Constitution v1 (Draft)** — especially the principles that all transactions require fees and that fees are consensus costs.
- **NYX Not-To-Do List** — especially the rejections of zero-fee systems, hidden subsidies, and token-as-legitimacy governance.
- **Threat Model v1** — especially the assumption of permanent adversaries and the prohibition of trust-based security.

If any statement here conflicts with those documents, those documents prevail.

---

## 1. Executive Statement

NYX exists to build a sustainable digital order that does not rely on human goodwill. In such a system, **cost is not optional**; it is a security primitive.

NYX therefore requires:

- a **protocol-native unit of cost** (**NYX Token**), and
- **protocol-enforced fees** for any shared-state impact,

to ensure three non-negotiables:

1. **Enforceable scarcity** (metering shared resources)
2. **Abuse resistance** (spam/Sybil/DoS become expensive by default)
3. **Self-funding security** (sustained defense without depending on donations, benevolent operators, or centralized revenue collectors)

> **NYX Token is justified by systems engineering, not by speculation.**

---

## 2. Design Objectives (What “Legitimate Economics” Means)

### 2.1 Objectives (MUST)

NYX economics MUST satisfy the following:

- **Internalize costs**: resource consumption must be paid by the consumer, not externalized to honest participants. **[NX-EC-§2.1.1]**
- **Be non-bypassable**: no privileged fee exemptions, no admin overrides, no “special lanes.” **[NX-EC-§2.1.2]**
- **Price abuse, not narratives**: the cheapest strategy for attackers must be prohibitively expensive. **[NX-EC-§2.1.3]**
- **Fund survivability**: the protocol must sustain security and critical operations under adversarial conditions. **[NX-EC-§2.1.4]**
- **Preserve governance safety**: economic stake MUST NOT automatically confer unconstrained political power. **[NX-EC-§2.1.5]**
- **Remain auditable**: value routing must be objectively verifiable and monitorable. **[NX-EC-§2.1.6]**

### 2.2 Explicit Non-Goals (MUST NOT)

NYX economics MUST NOT:

- depend on speculative price appreciation for security.
- subsidize usage with hidden inflation or opaque off-chain deals.
- create transferable reputation markets.
- treat token ownership as default legitimacy for governance.

---

## 3. Why NYX Token Must Exist

### 3.1 A protocol needs a native, censorship-resistant unit of cost

A protocol cost mechanism must be:

- **Consensus-enforced** (not policy-enforced)
- **Universally payable** (not permissioned by external intermediaries)
- **Non-revocable** by any single actor

A protocol-native token is the simplest mechanism that meets these constraints.

**NYX Token exists primarily as**:

- the default **fee payment asset** for protocol actions,
- the **unit-of-account** for scarce resource pricing,
- the settlement medium enabling NYX layers to remain independent of any single external rail.

### 3.2 External fee assets alone introduce structural dependency risk

Relying solely on external assets (stablecoins or other chains’ tokens) creates failure modes NYX cannot constitutionally accept:

- censorship/freeze risk,
- permissioned access risk,
- dependency on external monetary policy,
- weakened internal security budgeting.

Therefore NYX MUST have a protocol-native unit that remains usable even when external systems are hostile. **[NX-EC-§3.2.1]**

### 3.3 The token is not equity and does not imply a cashflow claim

NYX Token MUST NOT be framed as a shareholder claim on protocol revenues, nor as an entitlement to distributions. **[NX-EC-§3.3.1]**

NYX value accrual is primarily **work-based** (security provision, verifiable infrastructure services), not passive ownership.

---

## 4. Why Fees Are Structurally Required

### 4.1 Fees are consensus costs (not rent)

NYX fees represent the cost of changing shared state and consuming shared resources:

- bandwidth / propagation,
- computation / execution,
- persistent state / storage,
- privacy overhead (verification, relaying, anti-correlation constraints).

Fees are not punishment and not “revenue extraction.” They are the protocol’s **immune system**.

### 4.2 Non-zero fees are a constitutional invariant

Any action that creates, mutates, or preserves protocol-relevant state MUST incur a non-zero, protocol-enforced cost. **[NX-EC-§4.2.1]**

A zero-fee lane is not a UX feature. It is an attack surface.

### 4.3 Fee fairness is causality: “pay for the scarcity you consume”

NYX fee legitimacy is grounded in a simple rule:

> **The party imposing cost on the shared system pays the cost.**

This prevents hidden subsidies, which otherwise become:

- spam magnets,
- governance capture vectors,
- and long-term technical debt.

---

## 5. What Fees Price (Principles Only, No Parameters)

NYX SHOULD map fees to measurable resource consumption.

### 5.1 Primary fee surfaces

NYX MAY price actions over these surfaces:

1. **State Write Cost** — persistent shared state growth and maintenance.
2. **Verification Cost** — consensus computation, proof verification, validity/fraud checks.
3. **Congestion Cost** — contention for inclusion and propagation.
4. **Privacy Infrastructure Cost** — relaying, gateway mediation, anti-correlation overhead.

### 5.2 Pricing must be objective and non-waivable

If dynamic pricing exists, it MUST be:

- objectively measurable,
- consensus-verifiable,
- and non-waivable by privileged roles.

**No discretionary fee reduction** is allowed. **[NX-EC-§5.2.1]**

### 5.3 Predictability is desirable; subsidies are optional and must be explicit

NYX SHOULD aim for predictability for honest usage.

If predictability requires subsidies, those subsidies MUST be explicit, auditable, and non-discretionary. **[NX-EC-§5.3.1]**

### 5.4 Action → Resource → Fee Component Mapping (Non-Parametric)

NYX fees SHOULD be defined as an **additive fee vector** per action, rather than a single opaque number.

- **Base Component(s)** price the measurable resource being consumed.
- **Congestion Component(s)** price contention for inclusion.
- **Abuse Component(s)** price attack-shaped usage patterns.

Implementations SHOULD keep this mapping explicit so economic behavior is explainable, auditable, and hard to quietly manipulate.

| Action (Conceptual) | Primary Scarcity Consumed | Fee Component(s) (Conceptual) | Notes / Rationale |
|---|---|---|---|
| Create on-chain identity anchor | Persistent state growth | **State Write Fee** | Anchoring identity state must not be free; prevents anchor spam. |
| Rotate identity anchor / lineage update | Verification + state mutation | **Verify Fee** + **State Write Fee** | Rotation is a privacy primitive; costs must be real but not punitive. |
| Destroy identity state marker | State mutation | **State Write Fee** | Destruction is irreversible; must be consensus-enforced and non-free. |
| Submit a transaction that mutates shared state | Execution + propagation | **Execution Fee** + **Congestion Premium** | The canonical “consensus cost” surface. |
| Deploy/upgrade code (where applicable) | Large state + review risk | **State Write Fee** + **Risk Surcharge** | Deployment is a systemic risk surface; pricing discourages churn. |
| Large calldata / large payload actions | Bandwidth + storage pressure | **Bandwidth Fee** + **State Write Fee** | Prevents bloating via cheap payload stuffing. |
| On-chain verification of ZK proofs (if used) | Verification compute | **Verify Fee** | Proof verification must be priced to avoid proof-spam as DoS. |
| Gateway session initiation (NYX-mediated Web2 access) | Relay capacity + anti-correlation overhead | **Relay Fee** | Prices privacy-critical mediation; keeps the Gateway from becoming a free proxy. |
| Gateway relay bandwidth / egress | Bandwidth + operational cost | **Relay Fee** (metered) | Prevents turning NYX into a bandwidth subsidy for abuse. |
| Privacy pool join/split/merge (if applicable) | Proof + state | **Verify Fee** + **State Write Fee** | Privacy operations must remain economically sustainable. |
| Governance proposal submission | Attention + coordination cost | **Anti-Spam Fee** (or bond) | Prevents proposal spam and governance DoS. |
| Governance voting action | Inclusion bandwidth | **Minimal Execution Fee** | Keeps governance actions non-free without pricing them out. |
| Arbitration/dispute request (if applicable) | Coordination + state | **Anti-Spam Fee** + **State Write Fee** | Prevents griefing through frivolous disputes. |

**Hard rules**:

- Fee components MUST be **objective**, **consensus-verifiable**, and **non-waivable**. **[NX-EC-§5.4.1]**
- Any “discount” mechanism MUST be explicit, universally accessible under the same objective conditions, and auditable. **[NX-EC-§5.4.2]**
- Actions that increase long-lived state MUST be priced so that persistent bloat is never the cheapest attack. **[NX-EC-§5.4.3]**

### 5.5 Fee Function (Formal, Non-Parametric)

NYX SHOULD define fees using an additive fee function over objective measurements:

> **Fee(Action) = Σᵢ Componentᵢ(Action)**

Where each component MUST satisfy:

- **Non-negativity**: Componentᵢ(Action) ≥ 0. **[NX-EC-§5.5.1]**
- **Monotonicity**: increasing measured consumption of the priced resource MUST NOT reduce the component. **[NX-EC-§5.5.2]**
- **Local explainability**: each component must correspond to one scarcity surface and be independently interpretable. **[NX-EC-§5.5.3]**
- **No privileged toggles**: components must not be conditionally disabled by role, identity, or off-chain agreements. **[NX-EC-§5.5.4]**

This structure makes fee manipulation harder, because any attempted change must be explicit: *which component changed, and which scarcity it reprices*.

### 5.6 Fee Component Registry (Schema-Level Expectations)

NYX implementations SHOULD expose a registry of fee components with the following metadata (on-chain or equivalently verifiable):

- `component_id` (stable identifier)
- `scarcity_surface` (state/compute/bandwidth/privacy)
- `measurement_basis` (what is measured; objective)
- `update_rule` (how the component evolves; objective)
- `accounting_destination` (which fee bucket it routes to)

A component is invalid if it cannot be mapped to a measurable scarcity surface.

---

## Appendix B — Fee Sponsorship & Meta-Transaction Guardrails

Fee sponsorship (including meta-transactions) is allowed only if it does not create a bypass lane, does not introduce hidden subsidies, and does not increase linkability.

### B.1 Definition

A **sponsored action** is an action where the payer of protocol fees is not the direct originator of the action.

Sponsorship changes *who pays*, not *what is owed*.

### B.2 Non-bypassable fee rule

- A sponsored action MUST pay the same fee vector as the equivalent non-sponsored action. **[NX-EC-§B.2.1]**
- Sponsorship MUST NOT reduce any component to zero for state transitions. **[NX-EC-§B.2.2]**
- Sponsorship MUST NOT rely on privileged exemptions, partner lanes, or private allowlists. **[NX-EC-§B.2.3]**

### B.3 Explicitness and auditability

- Any sponsorship program MUST be explicit, rule-defined, and auditable (no off-chain deals with on-chain consequences). **[NX-EC-§B.3.1]**
- If sponsorship is funded by protocol reserves, it MUST follow the reserve outflow lifecycle requirements (timelock, caps, events). **[NX-EC-§B.3.2]**

### B.4 Anti-linkability constraints

Sponsorship MUST NOT become a correlation oracle.

- Sponsorship MUST NOT require stable identifiers from the originator beyond what the underlying action already reveals. **[NX-EC-§B.4.1]**
- Sponsorship mechanisms SHOULD support context separation so that repeated sponsorship does not produce a durable linkage token. **[NX-EC-§B.4.2]**

### B.5 Minimal sponsorship registry (schema-level)

Implementations SHOULD expose a registry for sponsorship programs with:

- `program_id`
- `eligibility_rule_hash` (objective rule)
- `payer_source` (who funds it)
- `scope` (which actions may be sponsored)
- `limits` (caps, rate limits)

---

## Appendix D — Privacy Parity Invariant

NYX MUST avoid an economics-driven privacy collapse where privacy primitives become unusable due to punitive pricing.

### D.1 Equivalence classes

Define an **equivalence class** of actions by objective resource measurements:

- state writes (quantity/size)
- verification work (units)
- execution work (units)
- bandwidth (units)

Two actions are **economically equivalent** if these measurements are equal under the same fee component registry.

### D.2 Parity requirement

- For economically equivalent actions, the fee vector MUST NOT differ except by objectively measured additional scarcity consumption. **[NX-EC-§D.2.1]**
- Fee policy MUST NOT introduce punitive differentials solely because an action is privacy-preserving. **[NX-EC-§D.2.2]**

### D.3 Parity justification

If a privacy-preserving action is more expensive, the implementation MUST be able to produce an objective explanation in terms of component measurements (e.g., higher verify units). **[NX-EC-§D.3.1]**

---

## 6. Value Return: How Fees Flow Back Into System Sustainability

NYX economics must close a loop: **usage → fees → security & critical operations → survivability → continued usage**.

### 6.1 Principle: fees fund survival, not narratives

Fee flows SHOULD prioritize:

- **Security compensation** (consensus participants, provers/verifiers, security-critical work)
- **Protocol reserves** (buffer for adversarial shocks, incident response, long-term security spend)
- **Critical infrastructure markets** (privacy-critical services paid for verifiable delivery)

### 6.2 Minimal, governance-safe fee routing buckets

NYX SHOULD route protocol fees into a small set of auditable buckets:

1. **Security Bucket** — pays verifiable security work.
2. **Reserve Bucket** — accumulates a buffer with explicit rules.
3. **Infrastructure Bucket** — funds privacy-critical infrastructure via verifiable service mechanisms.
4. **Supply Sink (Optional)** — burning/locking MAY exist as a structural control, not a promise.

Routing MUST be on-chain auditable. **[NX-EC-§6.2.1]**

### 6.3 “Token holders are not entitled” is a stability feature

NYX MUST avoid designs where fee routing becomes a political dividend.

Protocol sustainability must remain defensible even when token ownership concentrates.

### 6.4 Reserve Control Rules (Template — Rule-Governed, Not Discretionary)

NYX reserves exist to absorb adversarial shocks and finance security-critical work without introducing discretionary power.

**Reserve design MUST satisfy**:

- **Rule-governed outflows**: every outflow must be authorized by explicit on-chain rules, not by informal authority. **[NX-EC-§6.4.1]**
- **Delay by default**: reserve outflows MUST be time-delayed (non-zero timelock) with public visibility and cancelability. **[NX-EC-§6.4.2]**
- **Rate limits**: reserve outflows MUST be bounded by explicit caps per epoch/window (spending velocity). **[NX-EC-§6.4.3]**
- **Narrow spend categories**: outflows MUST declare a destination category (Security / Infrastructure / Incident Response / Protocol Maintenance) and MUST NOT route to generic “holder distributions.” **[NX-EC-§6.4.4]**
- **Auditable traceability**: every outflow must emit structured events sufficient for independent monitoring and forensic review. **[NX-EC-§6.4.5]**

**Recommended reserve rails (conceptual)**:

1. **Routine Rail** — scheduled, small, predictable spending for security maintenance.
2. **Incident Rail** — bounded emergency spending for defined incident classes.
3. **Strategic Rail** — slow, time-delayed spending for long-horizon investments.

### 6.5 Emergency Semantics (Template — Emergency Can Only Remove Capabilities)

NYX must survive crises without creating a “temporary dictator.” Therefore:

- Emergency mechanisms MUST be **restrictive** (pause/slow/raise-cost), not permissive (unbounded spend, secret actions). **[NX-EC-§6.5.1]**
- An emergency brake MAY:
  - pause specific outflow rails,
  - increase anti-abuse surcharges,
  - tighten inclusion constraints,
  - reduce system surface area.

- An emergency brake MUST NOT:
  - create new spending authority,
  - bypass timelocks,
  - introduce privileged fee exemptions,
  - authorize opaque off-chain settlements.

Emergency is a **circuit breaker**, not an executive branch.

### 6.6 Security Budget Rules (Template — Coverage Without Narratives)

NYX security spending should be designed so that the protocol can remain secure even in hostile market regimes.

NYX SHOULD separate security funding into two categories:

1. **Algorithmic Security Compensation** — predictable payments tied to verifiable security work (consensus participation, proof verification, infrastructure service delivery).
2. **Programmatic Security Spend** — bounded, time-delayed grants for audits, bug bounties, incident response, and critical security research.

**Constraints**:

- Security compensation MUST be primarily **work-based** and verifiable, not a passive entitlement. **[NX-EC-§6.6.1]**
- Programmatic security spend MUST be bounded by explicit caps and delays, and MUST be auditable end-to-end. **[NX-EC-§6.6.2]**
- If security funding depends on discretionary fundraising or insider decisions, the design SHOULD be treated as unstable and capture-prone.

### 6.7 Reserve and Outflow Lifecycle (Interface-Level Template)

This section defines a **minimal outflow lifecycle** that prevents reserve capture without requiring trust.

#### 6.7.1 Lifecycle states

- **Proposed**: an outflow request exists but cannot execute yet.
- **Executable**: timelock elapsed and all objective conditions satisfied.
- **Executed**: outflow completed and recorded.
- **Cancelled**: outflow invalidated by objective rule (e.g., emergency mode, expiry, or governance cancellation).

#### 6.7.2 Required outflow fields

Every reserve outflow request MUST include:

- `outflow_id` (unique)
- `category` (Security / Infrastructure / IncidentResponse / ProtocolMaintenance)
- `amount` (asset and quantity)
- `destination` (on-chain address or verifiable sink)
- `earliest_execute_time` (timelock)
- `expiry_time` (prevents stale execution)
- `justification_hash` (hash pointer to an immutable public rationale)
- `proposer` (record only; does not grant privilege)

Outflows missing any field are invalid. **[NX-EC-§6.7.1]**

#### 6.7.3 Required events (auditability)

Implementations MUST emit structured events for:

- `ReserveOutflowProposed(outflow_id, category, amount, destination, earliest_execute_time, expiry_time, justification_hash)`
- `ReserveOutflowExecuted(outflow_id, amount, destination)`
- `ReserveOutflowCancelled(outflow_id, reason_code)`

Absence of these events is non-compliant. **[NX-EC-§6.7.2]**

#### 6.7.4 Emergency interaction rule

If **Emergency Mode** is active, reserve outflows MUST be restricted to a pre-declared allowlist of incident classes, and MUST NOT bypass timelocks or caps. **[NX-EC-§6.7.3]**

### 6.8 Emergency Mode (Minimal Interface Template)

Emergency Mode exists to reduce blast radius, not to grant authority.

Implementations SHOULD support:

- `EnterEmergencyMode(reason_code)`
- `ExitEmergencyMode()`

**Hard constraints**:

- Entering emergency mode MUST NOT create new spending authority.
- Emergency mode MAY only pause/slow/raise-cost; it MUST NOT whitelist fee exemptions.
- Emergency mode transitions MUST be publicly visible and auditable.

### 6.9 Infrastructure Market Requirements (Relay/Gateway)

NYX may fund privacy-critical infrastructure (e.g., relays, gateway mediation) only through mechanisms that remain **verifiable, non-discretionary, and capture-resistant**.

Infrastructure funding mechanisms MUST satisfy:

- **Pay-for-verifiable-service**: payments MUST be tied to objectively verifiable delivery signals, not off-chain reputation. **[NX-EC-§6.9.1]**
- **No privileged routing**: infrastructure markets MUST NOT introduce whitelist lanes that function as fee bypasses. **[NX-EC-§6.9.2]**
- **No identity linkage pressure**: service markets MUST NOT require stable identifiers that increase correlation risk. **[NX-EC-§6.9.3]**
- **No anti-abuse circumvention**: infrastructure MUST NOT be incentivized to bypass external platform friction controls. **[NX-EC-§6.9.4]**

Implementations SHOULD emit a minimal, auditable trace that links **service delivery → fee payment** without introducing long-lived identifiers.

### 6.10 Fee Component → Accounting Destination Map (Conceptual)

NYX SHOULD map each fee component to a default accounting destination (bucket). This is not a parameter schedule; it is a **legibility requirement**.

| Fee Component | Default Destination (Bucket) | Rationale |
|---|---|---|
| **Execution Fee** | Security Bucket | Pays consensus execution work; aligns cost with liveness and correctness. |
| **Verify Fee** | Security Bucket | Pays verifiable verification work (e.g., ZK verification). |
| **Congestion Premium** | Security Bucket (and/or Reserve) | Prices inclusion scarcity; can strengthen security budget under attack regimes. |
| **State Write Fee** | Reserve Bucket (and/or Supply Sink) | Discourages persistent bloat; funds long-horizon maintenance and incident buffers. |
| **Bandwidth Fee** | Security / Infrastructure Bucket | Prices propagation/bandwidth; prevents payload stuffing; supports network sustainability. |
| **Relay Fee** | Infrastructure Bucket | Funds privacy-critical mediation capacity; prevents NYX becoming a free proxy. |
| **Anti-Spam Fee / Bond** | Supply Sink and/or Reserve (rule-defined) | Prevents governance/dispute spam; bonds enable slashing-compatible accountability where applicable. |

**Hard constraints**:

- Each fee component MUST declare an `accounting_destination` in the Fee Component Registry. **[NX-EC-§6.10.1]**
- Changing a component’s destination MUST be an explicit governance action with a timelock and a public rationale hash. **[NX-EC-§6.10.2]**
- Destinations MUST NOT create “holder dividend” defaults. **[NX-EC-§6.10.3]**

---

## Appendix C — Service Receipt Schema

NYX infrastructure funding requires a minimal notion of **verifiable service delivery** without creating long-lived identifiers.

A **Service Receipt** is a protocol-verifiable artifact linking **service delivery → eligibility for payment**, while preserving non-linkability.

### C.1 Required fields (normative)

A Service Receipt MUST include:

- `receipt_id` (unique)
- `service_type` (relay/gateway/other)
- `measurement_window` (start_time, end_time)
- `metered_units` (objective units)
- `payer_commitment` (commitment to payer context; not a stable identifier)
- `provider_commitment` (commitment to provider context; not a stable identifier)
- `context_handle` (domain separation)
- `nonce` (anti-replay)
- `verification_artifact` (proof or signature bound to context)

Receipts missing any field are invalid. **[NX-EC-§C.1.1]**

### C.2 Anti-linkability constraints

- Receipts MUST be domain-separated by `context_handle` and MUST NOT be reusable across contexts. **[NX-EC-§C.2.1]**
- Receipts MUST NOT embed stable identifiers (accounts, device fingerprints, persistent provider IDs). **[NX-EC-§C.2.2]**

### C.3 Payment linkage rule

A payment mechanism MUST be able to validate that:

1. the receipt is valid for the declared service type and measurement window, and
2. the receipt has not been replayed,

without requiring the receipt to disclose linkable metadata.

---

## 7. Governance Safety: Economic Power ≠ Political Power

NYX explicitly rejects token ownership as default legitimacy.

### 7.1 Token MAY be used as bond, not ballot

NYX MAY require bonding for certain roles (e.g., providing verifiable infrastructure), because bonds:

- create slashing-compatible accountability,
- impose measurable cost on misbehavior,
- are enforceable by consensus.

But bond-based participation MUST NOT imply unconstrained governance authority. **[NX-EC-§7.1.1]**

### 7.2 Constitutional constraints override economic interests

Governance outcomes MUST remain bounded by constitutionally frozen invariants.

> **Buying the token must not buy the system.**

### 7.3 Economic Parameter Governance Boundary

NYX MUST treat economic changes as attack surfaces. Parameter changes therefore require **classification**, **procedural constraints**, and **monotone safety**.

#### 7.3.1 Parameter classes

- **Class F (Frozen)** — cannot change within v1. Changes define a new major version.
  - Examples: non-zero fee invariant; no privileged fee bypass; no hidden subsidies; token ownership ≠ default legitimacy; emergency can only remove capabilities.

- **Class C (Constrained)** — changeable only under strict conditions; changes MUST NOT weaken protections.
  - Examples: fee function form; fee component registry schema; reserve outflow lifecycle requirements; required audit events.

- **Class P (Policy / Calibration)** — numeric parameters and thresholds that tune behavior without changing structure.
  - Examples: fee component coefficients; timelock durations; spending caps; congestion curve parameters.

#### 7.3.2 Change requirements (normative)

- Any economic change MUST declare its parameter class and MUST NOT be bundled with unrelated changes. **[NX-EC-§7.3.1]**
- Class C changes MUST be **monotone-safe**: they may tighten constraints, increase auditability, or reduce privilege; they MUST NOT introduce new bypasses or discretionary authority. **[NX-EC-§7.3.2]**
- All changes MUST publish a `justification_hash` that points to an immutable rationale and impact analysis. **[NX-EC-§7.3.3]**
- All changes MUST be time-delayed and cancelable (timelock + expiry). **[NX-EC-§7.3.4]**

### 7.4 Parameter Mutability Matrix (v1)

| Economic Item | Class | Notes |
|---|---:|---|
| Non-zero fee requirement for state transitions | F | Constitutional invariant. |
| No privileged fee bypass / exemptions | F | Any exemption is structural capture. |
| Fee function form (additive fee vector) | C | May be extended only if explainability and non-waivability remain. |
| Fee component registry schema + required metadata | C | Must remain measurable and auditable. |
| Reserve outflow lifecycle + required events | C | Must remain timelocked, capped, and auditable. |
| Emergency semantics (restrictive-only) | F | Emergency cannot grant new powers. |
| Default bucket destinations for fee components | P/C | Routing exists; destinations change via explicit governance with timelock. |
| Numeric fee calibration (coefficients, curves) | P | Must pass conformance tests; must not price privacy out by design. |
| Spending caps / timelock durations | P | Must not permit reserve raid behavior. |

---

## Appendix A — Economic Change Control

Economic changes are first-class attack surfaces. NYX therefore requires a change-control process that is explicit, time-delayed, cancelable, and testable.

### A.1 Change package schema (normative)

Any economic change MUST be submitted as a **Change Package** containing:

- `change_id` (unique)
- `parameter_class` (F/C/P)
- `affected_components` (fee components, reserves, routing, markets)
- `justification_hash` (immutable rationale)
- `impact_analysis_hash` (immutable analysis; includes expected test outcomes)
- `timelock_tier` (objective)
- `earliest_execute_time`
- `expiry_time`

Missing fields invalidate the change. **[NX-EC-§A.1.1]**

### A.2 Non-bundling rule

- A Change Package MUST NOT bundle unrelated changes. **[NX-EC-§A.2.1]**
- A Change Package MUST declare which conformance tests (Section 9.2) it could affect and why it still passes. **[NX-EC-§A.2.2]**

### A.3 Timelock tiers (template)

- **Tier P (Policy/Calibration)**: shortest timelock.
- **Tier C (Constrained structure)**: longer timelock + stricter review requirements.
- **Tier F (Frozen)**: not executable in v1.

The system MUST be able to enforce different timelock tiers by objective classification. **[NX-EC-§A.3.1]**

### A.4 Cancelability and expiry

- Every Change Package MUST be cancelable before execution and MUST expire if not executed by `expiry_time`. **[NX-EC-§A.4.1]**
- Emergency Mode MUST be able to block execution of pending economic changes (restrictive-only rule). **[NX-EC-§A.4.2]**

### A.5 Emergency constraint on changes

During Emergency Mode:

- Changes MAY tighten constraints, raise abuse costs, pause rails, or reduce surface area.
- Changes MUST NOT reduce fees, lower caps, shorten timelocks, or introduce exemptions. **[NX-EC-§A.5.1]**

---

## Appendix E — MEV & Orderflow Capture Policy

NYX MUST treat orderflow and inclusion as economic attack surfaces.

### E.1 No privileged orderflow lanes

- The protocol MUST NOT introduce private/partner orderflow lanes that bypass public inclusion rules. **[NX-EC-§E.1.1]**
- Inclusion and ordering rules SHOULD be publicly describable and monitorable. **[NX-EC-§E.1.2]**

### E.2 No off-chain side payments for ordering

Any mechanism that allows off-chain payments to influence inclusion/ordering is a capture vector and MUST be structurally discouraged or prohibited. **[NX-EC-§E.2.1]**

### E.3 Sequencer / proposer constraints (if applicable)

If an ordering role exists (sequencer/proposer), it MUST be constrained by:

- objective inclusion rules,
- auditable outputs,
- and a path toward reduced discretionary control.

### E.4 Monitoring signals

Implementations SHOULD monitor:

- actor-correlated inclusion advantages,
- unexplained priority anomalies,
- repeated ordering patterns inconsistent with declared rules.

---

## 8. Adversarial Review: If I Wanted to Break NYX Economics

This section is intentionally hostile. The goal is to pressure-test legitimacy.

### 8.1 Attack A: Create a “free lane” (fee bypass)

**Strategy**: introduce exemptions (partners, whitelists, admin relays, fee rebates), then route large volumes through them.

**Failure mode**: spam becomes cheap; exemptions become power; capture becomes inevitable.

**Countermeasure**:

- Fee exemptions MUST NOT exist. **[NX-EC-§8.1.1]**
- Any rebate/subsidy MUST be explicit, protocol-enforced, and universally accessible under the same objective conditions. **[NX-EC-§8.1.2]**

### 8.2 Attack B: Externalize costs via hidden subsidies

**Strategy**: claim “low fees” while secretly paying with inflation, treasury leakage, or opaque off-chain deals.

**Failure mode**: long-run insolvency and governance bribery.

**Countermeasure**:

- No hidden subsidies: if costs are paid, payers and rules must be explicit and auditable. **[NX-EC-§8.2.1]**
- Reserve spending MUST be rule-governed and transparent.

### 8.3 Attack C: Congestion griefing / fee volatility exploitation

**Strategy**: spike demand to raise fees, then force honest users out; or manipulate inclusion markets to create instability.

**Failure mode**: liveness for honest users collapses during attacks.

**Countermeasure**:

- Fee design SHOULD include objective congestion pricing and denial-of-service hardening.
- The system SHOULD separate “inclusion priority” from “state bloat incentives,” so attackers cannot cheaply grow persistent state.

### 8.4 Attack D: Governance capture via “token = vote” shortcuts

**Strategy**: accumulate token, pass proposals routing fees to holders or weakening constraints.

**Failure mode**: NYX becomes a shareholder protocol; capture is trivial.

**Countermeasure**:

- Token ownership MUST NOT be default governance legitimacy. **[NX-EC-§8.4.1]**
- Economic parameters touching invariants MUST require constitution-bound processes and hard limits.

### 8.5 Attack E: Reserve raid (treasury becomes a honeypot)

**Strategy**: create emergency spending powers, then justify “urgent” drains.

**Failure mode**: insiders and coalitions convert reserves into private benefit.

**Countermeasure**:

- Reserve outflows MUST be governed by explicit, time-delayed, auditable rules.
- No discretionary “god-mode” emergency spending.

### 8.6 Attack F: Privacy tax inversion (make privacy unaffordable)

**Strategy**: manipulate fee policy so privacy-preserving actions become prohibitively expensive, forcing users into linkable alternatives.

**Failure mode**: privacy collapses economically even if it remains cryptographically possible.

**Countermeasure**:

- Fee policy SHOULD avoid systematically penalizing privacy primitives.
- Privacy-critical infrastructure must have a sustainable funding path without requiring trusted sponsors.

### 8.7 Attack G: Dependency capture (force reliance on a Web2 rail)

**Strategy**: make fees effectively payable only through a permissioned on-ramp, turning the protocol into a choke point.

**Failure mode**: censorship becomes easy.

**Countermeasure**:

- NYX MUST remain payable without dependence on a single external intermediary. **[NX-EC-§8.7.1]**

### 8.8 Economic Attack Surface Index (Mapping)

This index ties **attack vectors → economic surfaces → structural controls → observability → emergency levers**.

| Attack Vector | Economic Surface | Primary Structural Control | Monitoring Signal | Emergency Lever |
|---|---|---|---|---|
| Fee bypass / exemptions | Fee enforcement | No privileged toggles; registry-required components | Bypass Test; component breakdown per action | Raise anti-abuse surcharges; tighten inclusion constraints |
| Hidden subsidies | Reserves / accounting | Rule-governed outflows + required events | Hidden Subsidy Test; reserve outflow events | Pause outflow rails; tighten caps |
| Reserve raid | Reserves | Timelock + caps + narrow categories | Reserve Raid Test; spending velocity | Restrict outflows to incident allowlist |
| Congestion griefing | Inclusion market | Objective congestion pricing; separate from state-bloat incentives | Congestion indicators; fee composition shifts | Raise congestion premium; tighten inclusion constraints |
| Persistent state bloat | State write | State Write Fee + (optional) sink; monotone pricing | State growth rate; state-write share of fees | Increase state-write component; restrict high-bloat actions |
| Proof-spam DoS | Verification | Verify Fee priced to verification cost | Verify-fee share; verification queue pressure | Raise verify component; cap proof-heavy actions |
| Privacy suppression via economics | Privacy primitives | Avoid systematic pricing out of privacy actions | Privacy Suppression Test; relative cost ratio | Adjust components to remove punitive differential |
| Infrastructure capture (relay/gateway) | Service markets | Pay-for-verifiable-service; no privileged routing | Service delivery → payment traceability | Pause payouts; switch to stricter verification |
| Dependency capture (single on-ramp) | Payability | Payability without single intermediary | Rail concentration metrics | Increase friction for dependency paths; keep alternatives live |
| MEV / orderflow capture (early warning) | Inclusion + routing | No privileged orderflow lanes; transparent inclusion rules | Inclusion anomalies; actor-correlated fee spikes | Tighten inclusion constraints; reduce surface area |

Any new economic feature MUST map into this index and declare its controls and signals. **[NX-EC-§8.8.1]**

---

## 9. Economic Health Invariants (Operationally Testable)

NYX SHOULD be evaluable by clear, non-narrative metrics:

1. **Cost Internalization**: system resource consumption correlates with fee payment.
2. **Abuse Price**: mass abuse is economically prohibitive at the protocol level.
3. **Security Budget Coverage**: security-critical operations can be funded without discretionary fundraising.
4. **Governance Non-Capture**: no direct pathway from token concentration to unconstrained power.
5. **Auditability**: fee routing and reserve changes are on-chain verifiable.

These are legitimacy tests. If they fail, the economics is illegitimate regardless of market price.

### 9.1 Observability and Monitoring Requirements

Because NYX assumes permanent adversaries, economic health MUST be monitorable.

Implementations SHOULD expose (on-chain or equivalently verifiable) signals for:

- **Fee composition** per action (which components were charged).
- **Congestion indicators** (objective inclusion pressure signals).
- **State growth rate** (long-lived state expansion velocity).
- **Reserve balance changes** (with outflow lifecycle events).
- **Security compensation flows** (work-delivery → payment traceability).

### 9.2 Conformance Tests (Non-Parametric)

An implementation SHOULD be considered economically non-compliant if any of the following tests fail:

1. **Bypass Test**: any role can execute a state transition with zero fee.
2. **Opacity Test**: fee cannot be decomposed into explainable components.
3. **Hidden Subsidy Test**: costs are paid from reserves without explicit, rule-governed authorization.
4. **Capture Test**: token ownership alone grants unconstrained governance power.
5. **Reserve Raid Test**: reserves can be spent without timelock, caps, and auditable events.
6. **Privacy Suppression Test**: privacy-preserving actions are systematically priced out relative to linkable alternatives without justification.

Passing these tests is stronger evidence of legitimacy than any market narrative.

---

## Appendix F — Economic Telemetry Spec

NYX economics is only defensible if it is observable. This appendix maps required signals to the minimal verifiable sources.

### F.1 Signal → Source mapping (conceptual)

| Signal | Minimal Verifiable Source | Notes |
|---|---|---|
| Fee composition per action | Fee Component Registry + per-action fee vector breakdown (or hash) | Must be reconstructible and non-opaque. |
| Congestion indicator | objective congestion index / inclusion pressure signal | Must not be discretionary. |
| State growth rate | state-write measurement basis over time | Used for bloat detection. |
| Reserve balance deltas | reserve outflow lifecycle events + balances | Must be end-to-end auditable. |
| Security compensation flows | work-delivery proofs/receipts → payments | Must be work-based, not entitlement. |
| Infrastructure payments | Service Receipts → payouts | Must not create stable identifiers. |
| Sponsorship activity | sponsorship registry + sponsored payment traces | Must not become a correlation oracle. |
| MEV/orderflow anomalies | inclusion traces + fee spikes + actor correlation | Early warning for capture. |

### F.2 Minimal event expectations (non-exhaustive)

Implementations SHOULD make it possible to derive:

- which fee components were charged for a given action,
- which accounting destinations received funds,
- which reserve rail (if any) executed an outflow,
- whether emergency mode changed state.

If these cannot be derived, the system is economically opaque and should be treated as non-compliant.

---

## 10. Hard Requirements (Non-Negotiable)

1. **Non-zero fees for state transitions**. **[NX-EC-§10.1.1]**
2. **No privileged fee bypass**. **[NX-EC-§10.1.2]**
3. **No hidden subsidies**. **[NX-EC-§10.1.3]**
4. **Fee routing auditable by consensus**. **[NX-EC-§10.1.4]**
5. **Token ownership ≠ default legitimacy**. **[NX-EC-§10.1.5]**

Any economic design violating these requirements is non-compliant with NYX.

---

## 11. Open Items (Intentionally Out of Scope)

The following are intentionally unresolved and MUST NOT be inferred from this document:

- Supply policy (fixed / elastic / hybrid)
- Parameter calibration (fee levels, routing proportions)
- Specific mechanism selections (burn/lock curves, market designs)
- Service market implementations (relay/gateway markets)

This is deliberate: **legitimacy first, parameters later**.

---

## 12. Freeze Boundary (v1)

For **NYX Economic Rationale v1**, the following sections are considered **frozen**:

- Section 2 (Objectives and Non-Goals)
- Section 4 (Why Fees Are Required)
- Section 6 (Value Return Principles)
- Section 7 (Governance Safety)
- Section 10 (Hard Requirements)

Any future revision that weakens these sections defines a new major version.

---

## 13. Summary

NYX Token exists because NYX requires a protocol-native unit that enforces scarcity and sustains survivability.

Fees are legitimate because they price consensus costs and internalize externalities.

Value returns to the system because a protocol that cannot fund security and critical operations becomes either:

- a spam economy,
- a captured platform,
- or a dead protocol.

NYX chooses a stricter path:

> **Sustainability is enforced by structure, not promised by narrative.**

---

## Appendix G — Cross-Document Integration Points

This appendix defines explicit hooks so later documents do not re-interpret economics.

### G.1 Governance_Model_v1.md hooks

Governance MUST reference and enforce:

- Change Package schema (Appendix A)
- Parameter classes F/C/P (Section 7.3)
- Reserve outflow lifecycle and required events (Section 6.7)
- Emergency semantics (Sections 6.5, 6.8)

### G.2 NYX_Architecture_v1.md hooks

Architecture MUST expose surfaces for:

- Fee Component Registry (Section 5.6)
- Fee Function (Section 5.5)
- Accounting destinations (Section 6.10)
- Service Receipt validation (Appendix C)
- Sponsorship registry (Appendix B)

### G.3 Threat_Model_v1.md hooks

Economic attack surfaces MUST map into:

- Economic Attack Surface Index (Section 8.8)
- Conformance tests (Section 9.2)

---

## Appendix H — Changelog

- v1 (Week 6): Initial executive-grade rationale, normative constraints, adversarial review, and governance boundaries.
- v1 (Week 6+): Added change control, sponsorship guardrails, service receipts, privacy parity invariant, MEV policy, telemetry mapping, and cross-document hooks.
