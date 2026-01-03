# Threat Model v1

## Introduction

This document defines the authoritative threat model for NYX.

NYX is designed under the assumption of a permanently adversarial environment. Power is not trusted, neutrality is insufficient, and human goodwill is explicitly excluded from the system’s security assumptions. This threat model therefore does not attempt to predict attacks; it constrains design. Its purpose is to define the maximum adversarial capabilities under which NYX must remain structurally functional.

The threat model is normative. It specifies the adversaries NYX is built to survive, the limits of their power, and the architectural consequences that follow. Any system behavior that relies on adversaries acting benevolently, rationally, or passively is considered invalid by definition.

Five adversary classes are considered:

- Nation-State Actors
- Platform-Level Adversaries
- Onchain Analytics Firms
- External Hackers
- Internal Malicious Actors

For each adversary class, this document defines:

- **Capabilities**: the realistic upper bound of technical, economic, legal, and coercive power
- **Attack Vectors**: the dominant mechanisms by which the adversary may attempt to compromise the system or its users
- **Assumed Threat Boundaries**: explicit statements of what the adversary is and is not assumed capable of doing
- **Implications for NYX Design**: non-negotiable architectural and governance constraints imposed by the threat

This model is derived from and subordinate to the NYX Constitution and the NYX Not-To-Do List. Together, they enforce the following axioms:

- Identity is protocol-native and never bound to real-world persons
- Wallets are replaceable tools, never sources of authority
- All state transitions impose economic cost
- All Web2 systems are adversarial inputs, never sources of truth
- Abuse-resistance and decentralization override efficiency and convenience

NYX does not seek safety through secrecy, compliance, or reputation. Resistance is encoded directly into protocol structure. Any attack that succeeds only by violating these assumptions is out of scope; any attack feasible within them must be survivable without discretionary intervention.

This document is a permanent design constraint. All architectural, cryptographic, governance, and implementation decisions must remain consistent with the adversarial realities defined herein.

---

## 1. Nation-State Actors

### Capabilities

Nation-state adversaries possess effectively unbounded legal authority within their jurisdictions, substantial financial resources, advanced cyber capabilities, intelligence services, and coercive power over individuals and infrastructure. They can mandate surveillance, compel cooperation from centralized intermediaries, restrict access to networks, and apply physical-world pressure.

### Attack Vectors

- Network-level surveillance, censorship, and traffic analysis
- Legal and regulatory coercion of developers, operators, and service providers
- Economic capture of consensus participants
- Intelligence-driven deanonymization and targeted enforcement

### Assumed Threat Boundaries

NYX assumes nation-states can fully compromise centralized infrastructure and coerce identifiable individuals. NYX does not assume nation-states can break modern cryptography or globally suppress all decentralized participants simultaneously.

### Implications for NYX Design

NYX must be jurisdiction-agnostic, censorship-resistant, and independent of real-world identity systems. No privileged access paths, compliance backdoors, or discretionary authorities may exist.

---

## 2. Platform-Level Adversaries

### Capabilities

Platform adversaries include centralized technology providers capable of deplatforming applications, terminating infrastructure access, enforcing policy restrictions, and collecting extensive user metadata.

### Attack Vectors

- Application removal and service denial
- Metadata surveillance and behavioral profiling
- Policy-based coercion and feature suppression

### Assumed Threat Boundaries

NYX assumes all Web2 platforms are adversarial and unreliable. Platform actors cannot directly violate consensus validity or cryptographic correctness.

### Implications for NYX Design

All Web2 dependencies must be optional, replaceable, and cryptographically wrapped. NYX must remain operational without reliance on any single platform, distribution channel, or service provider.

---

## 3. Onchain Analytics Firms

### Capabilities

Onchain analytics adversaries possess advanced data ingestion, clustering, and correlation capabilities, combining public ledger analysis with offchain data sources to infer identity and behavior.

### Attack Vectors

- Transaction graph analysis and clustering
- Cross-context behavioral correlation
- Collaboration with exchanges and regulators

### Assumed Threat Boundaries

NYX assumes all public onchain data will be exhaustively analyzed. Analytics firms are not assumed capable of breaking sound cryptographic unlinkability or zero-knowledge guarantees.

### Implications for NYX Design

NYX must minimize linkable metadata, enforce identity compartmentalization, and rely on zero-knowledge proofs for selective disclosure and verification.

---

## 4. External Hackers

### Capabilities

External hackers range from individual attackers to organized criminal groups with significant technical expertise, automation, and financial incentives.

### Attack Vectors

- Smart contract and protocol exploits
- Spam, Sybil, and denial-of-service attacks
- Phishing, malware, and key compromise

### Assumed Threat Boundaries

NYX assumes persistent hostile probing. Hackers are not assumed capable of breaking cryptographic primitives or violating consensus without sufficient economic control.

### Implications for NYX Design

Security must be enforced structurally through economic costs, formal verification, layered defenses, and robust key and identity management.

---

## 5. Internal Malicious Actors

### Capabilities

Internal adversaries include developers, validators, or governance participants with privileged access, system knowledge, or influence.

### Attack Vectors

- Introduction of backdoors or malicious updates
- Abuse of privileged roles or insider collusion
- Governance manipulation or silent rule changes

### Assumed Threat Boundaries

NYX assumes insiders may act maliciously. No individual or small group is trusted by default. Byzantine fault tolerance assumptions apply.

### Implications for NYX Design

All authority must be distributed, auditable, and revocable. Governance, upgrades, and enforcement must be explicit, transparent, and constitutionally constrained.


---

## Explicit Non-Goals

The following objectives are explicitly out of scope for NYX. Failure to achieve them is not considered a system failure.

- Preventing all individual user loss due to key compromise or phishing
- Providing anonymity against users’ own voluntary disclosure or operational mistakes
- Complying with jurisdiction-specific regulatory or surveillance requirements
- Guaranteeing uninterrupted availability under global-scale coordinated shutdowns
- Protecting against adversaries capable of breaking standard cryptographic primitives

NYX optimizes for structural resilience, not absolute protection or user safety guarantees.

---

## Failure Modes Under Assumption Violation

This section documents expected system behavior if core threat assumptions are violated.

- **Cryptographic Breakthrough**: If core cryptographic assumptions fail, identity unlinkability and transaction privacy may collapse. NYX does not attempt graceful degradation under cryptographic failure.
- **Global Validator Capture**: If a supermajority of consensus participants collude maliciously, protocol correctness cannot be guaranteed. The expected response is social-layer rejection and fork.
- **Total Platform Suppression**: If all access channels are censored simultaneously, NYX may become temporarily inaccessible but remains logically intact.
- **Complete Insider Collusion**: If all privileged actors collude, governance guarantees fail. Recovery depends on external community coordination.

These failure modes define hard limits beyond which protocol guarantees do not apply.

---

## Attack Surface Index

This index maps adversarial attack vectors to primary architectural surfaces.

| Adversary Class | Attack Vector | Primary Surface |
|---------------|---------------|----------------|
| Nation-State | Legal coercion | Identity, Governance |
| Nation-State | Network censorship | Networking, Client |
| Platform-Level | Deplatforming | Distribution, Access |
| Platform-Level | Metadata surveillance | Client, Gateway |
| Analytics Firms | Graph analysis | Ledger, Identity |
| Analytics Firms | Offchain correlation | Gateway, User OpSec |
| External Hackers | Contract exploits | Protocol Logic |
| External Hackers | Spam/Sybil | Economic Layer |
| Internal Actors | Backdoors | Codebase, Upgrade Path |
| Internal Actors | Governance manipulation | Governance Logic |

This index serves as a reference for architectural review and security validation.

