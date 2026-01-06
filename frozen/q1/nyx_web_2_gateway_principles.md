# NYX_Web2_Gateway_Principles.md

Version: v1 (Normative Protocol Principles)

---

## Normative Language

The key words **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** in this document are to be interpreted as described in RFC 2119.  

Each normative requirement is assigned a stable identifier in the form **[NX-§X.Y.Z]**.  

An implementation is considered **non-compliant** if it violates **any** requirement labeled **MUST** or **MUST NOT**.

---

## Executive Statement

> **NYX Web2 Gateway Principles define the enforced isolation of all Web2 interactions to maintain anonymity and security by design.**

This document is intentionally strict and non-negotiable.  

Any system architecture that:  
- trusts external Web2 services or data,  
- integrates Web2 content directly into core logic,  
- or retains stable identifiers across sessions,  

is explicitly **out of scope** for the NYX Web2 Gateway.  

NYX Web2 Gateway is not optimized for convenience or compliance.  
It is optimized for **adversarial resilience and non-linkability by structure**.

**Legitimate privacy in NYX** refers to the structural minimization of unnecessary data exposure, not the circumvention of rules, safeguards, or accountability mechanisms imposed by external systems. NYX does not seek to bypass controls; it seeks to avoid becoming a data source.

---

## 0. Threat Assumptions

NYX operates under a permanently adversarial model. All external (Web2) systems are treated as untrusted, mutable, and hostile by default. Platform-level actors are assumed to engage in surveillance, censorship, and profiling. No Web2 service or intermediary is expected to act benevolently or reliably. The Gateway design therefore treats any Web2 input as adversarial **by definition**, and no external platform is critical to core survival.

---

## 1. Non-Negotiable Invariants

The following invariants are mandatory architectural constraints. Violation of any invariant disqualifies an implementation.

### 1.1 Gateway Mediation  
- **[NX-1.1.1]** All Web2 interactions **MUST** be conducted exclusively via the NYX Gateway. No NYX component may directly access external (Web2) services.

### 1.2 Input Isolation  
- **[NX-1.2.1]** The Gateway **MUST** wrap and isolate all external inputs, downgrading them to a minimal safe form before any NYX core logic consumes them. Under no circumstance shall raw Web2 data or active content enter NYX unmediated.

### 1.3 Hostile Identifiers  
- **[NX-1.3.1]** The Gateway **MUST** treat all Web2-derived metadata and identifiers (e.g. cookies, IP addresses, device fingerprints) as hostile inputs. Such data carries **zero trust** and must be handled as transient, unprivileged information only.

### 1.4 External Independence  
- **[NX-1.4.1]** All Web2 dependencies **MUST** be optional and replaceable; the system **MUST NOT** rely on any single external platform for core functionality. NYX must remain fully operational without allegiance to any specific Web2 service or provider.

---

## 2. Forbidden Behaviors

The following behaviors are strictly prohibited. Any occurrence results in non-compliance.

### 2.1 Identity Linkage  
- **[NX-2.1.1]** The Gateway **MUST NOT** create, preserve, or allow any identity linkage across sessions, sites, or contexts. No stable identifier or correlation token may persist beyond its immediate Web2 context.

### 2.2 Anti-Abuse Circumvention  
- **[NX-2.2.1]** The Gateway **MUST NOT** bypass or weaken any rate limit, friction mechanism, or anti-abuse control imposed by external platforms. User convenience or throughput MUST NEVER trump abuse-resistance.

### 2.3 Regulatory Evasion  
- **[NX-2.3.1]** The Gateway **MUST NOT** facilitate regulatory evasion or malicious circumvention of legal/policy controls. No feature may be designed for the purpose of bypassing jurisdictional requirements or compliance measures.

### 2.4 Human Simulation  
- **[NX-2.4.1]** The Gateway **MUST NOT** actively simulate human behavior, evade detection mechanisms, or engage in adversarial adaptation against platform abuse detection systems.

---

## 3. Responsibility Boundaries

The following role boundaries are strict and enforceable:

- **Gateway** – Mediates all Web2 interactions. The Gateway performs data retrieval, filtering, and anonymization on behalf of NYX. It **MUST NOT** permit any direct or unfiltered channel between external services and NYX core (no privileged bypass or backdoor).

- **NYX Core** – Executes all internal protocol logic and state transitions. The core **MUST NOT** ingest or trust any external input except via the Gateway, and **MUST NOT** embed external identifiers or state into on-chain logic. All authoritative state, credit, and decisions are produced inside NYX.

- **Client Applications (SDK Integrations)** – Invoke external services solely through the Gateway. Any NYX-integrated application **MUST NOT** call or embed third-party Web2 APIs directly. All Web2 usage in the NYX context is funnelled through the Gateway wrapper.

*(Any role conflation or violation of these boundaries constitutes non-compliance.)*

---

## 4. Explicit Non-Goals

The following objectives are explicitly out of scope for the NYX Web2 Gateway (their absence is not considered a failure of the system):

- Defining any specific Gateway architecture, implementation, API, or SDK interface (the principles are implementation-agnostic).  
- Preserving user identity, personalization, or session continuity across Web2 interactions.  
- Optimizing for user convenience, low friction, or growth metrics at the expense of security/anonymity.  
- Achieving or prioritizing compliance with jurisdiction-specific regulations (neutrality to external policy is assumed).  
- Enforcing behavior-level anonymity policies or usage patterns – those are detailed in **Behavioral_Anonymity_Rules.md** (beyond the scope of this document).  
- Ensuring uninterrupted or successful access to external Web2 services under all conditions is not a goal of the Gateway.

---

## Freeze Boundary

For **NYX Web2 Gateway Principles v1**, the following sections are considered **constitutionally frozen**:

- Section 1: Non-Negotiable Invariants  
- Section 2: Forbidden Behaviors  

Any future revision that alters these sections defines a new major version. All other sections may be expanded in future iterations, but **MUST NOT** contradict the frozen principles above.

