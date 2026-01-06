# Key_Management_Model

Version: v1 (Responsibility Freeze — Week 5)
Status: Draft (Target: Q1 Freeze)
Owner: NYX Core
Date: 2026-02-01
Last-Modified: 2026-02-01
Related: Crypto_Stack_Selection_v1.md; NYX_Constitution_v1_draft.md; Threat_Model_v1.md; NYX_ZK-ID_Spec_v1.md; NYX_Web2_Gateway_Principles.md

---

## Normative Language

The key words **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** in this document are to be interpreted as described in RFC 2119.

Each normative requirement is assigned a stable identifier in the form **[NX-KM-§X.Y.Z]**.

---

## Executive Statement

NYX key management is designed to be:
- **non-discretionary** (no “support ticket” recovery),
- **non-custodial by default** (users own their secrets),
- **insider-hostile** (a single employee cannot become God),
- **rotation-native** (compromise leads to replace, not panic),
- **auditable without leaking** (events are visible, secrets are not).

This document freezes:
1) **Key responsibility model** — who can do what, and who cannot.
2) **Key lifecycle requirements** — generate, store, use, rotate, revoke, destroy.
3) **Separation-of-duties** — how NYX prevents one-key takeovers.

---

## 0. Scope

### 0.1 In Scope

- Subject (user) key responsibilities for identity and privacy.
- System/infrastructure keys required to operate NYX components.
- Issuer key governance for credentials.
- Mandatory controls for rotation, revocation, and incident response.

### 0.2 Out of Scope

- Concrete custody implementation choices (specific KMS/HSM vendor).
- Chain selection and chain transaction signature scheme details.
- UI/UX procedures (this is law, not interface).

---

## 1. Non-Negotiable Invariants (Constitutional)

### 1.1 No Human Trust

- **[NX-KM-§1.1.1]** NYX **MUST NOT** rely on any administrator, operator, or customer support agent to preserve or restore user identity control.
- **[NX-KM-§1.1.2]** No single organizational role **MAY** unilaterally decrypt user data or alter identity state.

### 1.2 Wallet ≠ Identity

- **[NX-KM-§1.2.1]** Chain transaction keys (wallet keys) **MUST NOT** be treated as NYX identity roots.
- **[NX-KM-§1.2.2]** Loss of a wallet **MUST NOT** equal loss of a NYX Identity.

### 1.3 Replaceability Over Permanence

- **[NX-KM-§1.3.1]** All non-subject keys used by NYX services **MUST** be replaceable without privileged “forever keys.”
- **[NX-KM-§1.3.2]** Any key that can silently change security guarantees is **forbidden**.

### 1.4 Secrets Never Become Logs

- **[NX-KM-§1.4.1]** Private keys, seeds, root secrets, recovery material, and plaintext sensitive payloads **MUST NOT** be logged.
- **[NX-KM-§1.4.2]** Telemetry **MUST** be designed to be useful without containing secrets.

### 1.5 NYX Services Cannot Decrypt Subject Content

- **[NX-KM-§1.5.1]** NYX services (Gateway/Core/Operators) **MUST NOT** possess the capability to decrypt subject end-to-end protected content.
- **[NX-KM-§1.5.2]** If any subject data is stored server-side, it **MUST** be stored as ciphertext such that compromise of NYX infrastructure does not reveal plaintext.
- **[NX-KM-§1.5.3]** Any feature that requires server-side plaintext access to subject-protected content is **forbidden** unless explicitly introduced in a new major version with threat-model justification.

---

## 2. Key Taxonomy (Frozen)

> A key is not “a key.” It is a contract: owner, purpose, scope, lifetime, rotation rules.

### 2.1 Subject-Controlled Keys (User Domain)

**K1 — Identity Root Secret (RS)**
- Owner: Subject
- Purpose: Root of NYX Identity control (derivation & lifecycle proofs)
- Storage: Subject secure storage only
- Lifetime: Long-lived, but rotation/recovery must create new material
- Compromise impact: Highest

**K2 — Identity Signing Key (ISK)**
- Owner: Subject
- Purpose: Sign NYX identity actions (application-layer)
- Derivation: MAY be derived/linked to RS via HKDF + domain separation
- Lifetime: Rotatable

**K3 — Context Keys (CK)**
- Owner: Subject
- Purpose: Per-context derivations to enforce unlinkability
- Scope: Single context only
- Lifetime: Short/ephemeral or context-bounded

**K4 — Session Keys (SK)**
- Owner: Subject + counterparty
- Purpose: Forward-secret channel encryption
- Lifetime: Ephemeral

**K5 — Chain Transaction Key (CTK)**
- Owner: Subject
- Purpose: Authorize transactions on the chosen chain environment
- Rule: Treated as transport/auth to chain, never identity

### 2.2 Issuer Keys (Credential Domain)

> Issuers can attest to claims (via credentials). They are **not** identity owners, not trust anchors, and not recovery agents.

**K6 — Issuer Signing Key (I-SIGN)**
- Owner: Issuer entity
- Purpose: Sign credentials used in ZK proofs
- Requirement: Must support rotation + revocation without issuer “god-mode” over identities

**K7 — Issuer Revocation/Registry Key (I-REG)**
- Owner: Issuer entity
- Purpose: Publish revocation updates (if signed)

#### 2.2.1 Issuer Set Model (Frozen)

- **[NX-KM-§2.2.1]** NYX **MUST** support an **Issuer Set** containing one or more issuers for any given claim domain.
- **[NX-KM-§2.2.2]** An Issuer Set **MUST** be represented explicitly as a versioned, auditable policy object (the **Verifier Acceptance Policy**) rather than an implicit “trusted list.”
- **[NX-KM-§2.2.3]** The Verifier Acceptance Policy **MUST** define, at minimum: issuer public keys (or key identifiers), validity windows, revocation endpoints/structures, and the acceptance rule (e.g., 1-of-N, K-of-N, or class-specific thresholds).
- **[NX-KM-§2.2.4]** Verifiers **MUST** evaluate proofs against the Verifier Acceptance Policy deterministically.
- **[NX-KM-§2.2.5]** An issuer **MUST NOT** be able to unilaterally alter verifier acceptance rules for previously issued credentials.

#### 2.2.2 Threshold & Diversification (Recommended Defaults)

> The goal is to avoid a single issuer becoming a structural single point of failure, while keeping v1 deployable.

- **[NX-KM-§2.2.6]** For v1, the default acceptance rule **MAY** be **1-of-N** for **low-stakes** claims (pure eligibility gating with low abuse impact).
- **[NX-KM-§2.2.7]** For **high-stakes** claims (e.g., high-value eligibility, actions with meaningful economic or governance impact), the acceptance rule **SHOULD** require diversification across independent issuers.
- **[NX-KM-§2.2.7a]** The **recommended default** for high-stakes claims is **2-of-3** across **independent** issuers.
- **[NX-KM-§2.2.7b]** High-stakes claims **MUST NOT** default to **1-of-1** acceptance unless the deployment is explicitly operating in **degraded mode** (Section 2.2.3) and publicly declares the reduced fault-tolerance.
- **[NX-KM-§2.2.7c]** A Verifier Acceptance Policy **MAY** choose stronger thresholds than 2-of-3 (e.g., 3-of-5) where appropriate, but **MUST** remain deterministic and auditable.
- **[NX-KM-§2.2.8]** Issuer diversification **MUST** be defined by structure (policy) and **MUST NOT** rely on informal trust, reputation, or discretionary verifier behavior.

#### 2.2.3 v1 Degraded Mode: Single Issuer (Allowed, Auditable)

- **[NX-KM-§2.2.9]** v1 deployments **MAY** operate with an Issuer Set of size 1 **only as a configuration-degraded mode**.
- **[NX-KM-§2.2.10]** Degraded mode **MUST** preserve the same interfaces and policy structures as multi-issuer mode (no special-case code paths).
- **[NX-KM-§2.2.11]** A deployment operating in degraded mode **MUST** publish an explicit statement of reduced fault-tolerance (SEV-1 blast radius) as part of the Verifier Acceptance Policy metadata.
- **[NX-KM-§2.2.12]** Upgrading from single-issuer to multi-issuer **MUST NOT** require identity takeover, administrator action, or any change that violates unlinkability constraints.

#### 2.2.4 Claim Risk Classification (Frozen)

> NYX treats “who can mint legitimacy” as a primary attack surface. Risk classification is structural, not narrative.

- **[NX-KM-§2.2.13]** Every Verifier Acceptance Policy **MUST** declare a `risk_class` for the claim domain: `LOW` or `HIGH`.
- **[NX-KM-§2.2.14]** If `risk_class` is missing, ambiguous, or unspecified, verifiers **MUST** treat it as `HIGH`.

**Definition: HIGH risk claim** — any claim whose acceptance can enable meaningful abuse or capture, including but not limited to:
- **[NX-KM-§2.2.15]** Authorizing or materially enabling **value transfer**, withdrawal, escrow release, credit extension, or fee reduction.
- **[NX-KM-§2.2.16]** Granting or influencing **governance power** (voting weight, proposal rights, treasury actions, upgrade influence).
- **[NX-KM-§2.2.17]** Granting **privileged protocol capabilities** (rate-limit bypass, anti-spam/friction reduction, elevated API permissions, operator-like actions).
- **[NX-KM-§2.2.18]** Creating **long-lived advantage** that is costly to reverse (persistent reputation thresholds, access to high-impact markets, irreversible entitlements).

**Definition: LOW risk claim** — claims whose acceptance is strictly scoped, low-blast-radius, and reversible:
- **[NX-KM-§2.2.19]** LOW risk claims **MUST** be context-bounded, have no direct value-transfer effect, and have limited blast radius (e.g., access gating for a low-impact context).

**Threshold mapping (enforced):**
- **[NX-KM-§2.2.20]** For `HIGH` risk claims, the Verifier Acceptance Policy **SHOULD** use diversified issuance with a recommended default of **2-of-3** independent issuers, and **MUST NOT** default to **1-of-1** except in degraded mode (Section 2.2.3).
- **[NX-KM-§2.2.21]** For `LOW` risk claims, the policy **MAY** use **1-of-N** acceptance.

**Independence requirements (minimum):**
- **[NX-KM-§2.2.22]** Issuers counted toward a threshold for `HIGH` risk claims **MUST** be independent in key custody and signing infrastructure (no shared signing keys, no shared signing service).
- **[NX-KM-§2.2.23]** The policy metadata **SHOULD** include issuer independence notes (e.g., distinct legal entities/jurisdictions), but independence **MUST** be enforceable at least at the cryptographic custody boundary.

### 2.3 NYX Service / Infrastructure Keys (System Domain)

**K8 — Service Identity Key (S-ID)**
- Owner: NYX service instance (non-human)
- Purpose: Authenticate services to each other; authorize narrowly scoped API actions

**K9 — TLS Private Key (TLS-PRIV)**
- Owner: NYX deployment
- Purpose: TLS termination (where applicable)

**K10 — Build/Release Signing Key (REL-SIGN)**
- Owner: NYX release process
- Purpose: Sign artifacts/binaries/config manifests

**K11 — Production Configuration Integrity Key (CFG-SIGN)**
- Owner: NYX deployment process
- Purpose: Sign/attest “what config is running”

> Note: System keys exist to prevent tampering and impersonation. They must never become a backdoor into user secrets.

---

## 3. Role & Responsibility Model (Frozen)

### 3.1 Roles

- **Subject**: controls RS and initiates identity lifecycle actions.
- **NYX Client**: executes crypto locally; MUST be capable of operating without trusting servers.
- **NYX Gateway**: mediates Web2 interactions; MUST NOT store stable identifiers.
- **NYX Core / Protocol**: validates proofs, enforces costs and invariants.
- **Issuer**: issues credentials; may revoke its own credentials; MUST NOT control identity state.
- **Verifier**: verifies proofs; MUST NOT demand extra identifiers.
- **Operator (Infra)**: deploys services; MUST NOT access user secrets.
- **Release Managers (Process Role)**: participate in release signing under quorum.

### 3.2 Responsibility Matrix (Who Can Do What)

**Subject MAY / MUST**
- **[NX-KM-§3.2.1]** Subject **MUST** generate RS locally using a secure RNG.
- **[NX-KM-§3.2.2]** Subject **MUST** keep RS under exclusive control.
- **[NX-KM-§3.2.3]** Subject **MAY** maintain backups of RS, but only in encrypted form (see Section 5).

**NYX Client MAY / MUST NOT**
- **[NX-KM-§3.2.4]** NYX Client **MUST** perform private-key operations locally when those operations are security-critical to identity/privacy.
- **[NX-KM-§3.2.5]** NYX Client **MUST NOT** upload RS or plaintext recovery material to any NYX service.

**NYX Core / Protocol MUST NOT**
- **[NX-KM-§3.2.6]** NYX Core **MUST NOT** possess any capability to derive, reconstruct, or request RS.
- **[NX-KM-§3.2.7]** NYX Core **MUST NOT** include discretionary override paths to change identity state.

**Operators MUST NOT**
- **[NX-KM-§3.2.8]** Operators **MUST NOT** have access to user private keys, RS, or plaintext sensitive data.
- **[NX-KM-§3.2.9]** Operators **MUST NOT** deploy any build artifact not signed by the release quorum.
- **[NX-KM-§3.2.9a]** Operators **MUST NOT** terminate or re-encrypt TLS traffic outside the NYX-controlled trust boundary in a way that introduces a third-party plaintext visibility point.
- **[NX-KM-§3.2.9b]** Production access credentials for operators **MUST** be short-lived and non-reusable (no long-lived static secrets).

**Issuers MAY / MUST NOT**
- **[NX-KM-§3.2.10]** Issuers **MAY** revoke credentials they issued.
- **[NX-KM-§3.2.11]** Issuers **MUST NOT** recover, seize, or freeze a subject’s identity.
- **[NX-KM-§3.2.12]** Issuers **MUST** rotate issuer signing keys with an auditable, verifiable chain of trust (see Section 7.1).
- **[NX-KM-§3.2.13]** Issuers **MUST** publish revocation information in a way verifiers can check without requiring stable subject identifiers.

**Verifiers MUST NOT / MUST**
- **[NX-KM-§3.2.14]** Verifiers **MUST NOT** demand stable identifiers, wallet addresses, or extra identifying material as a condition of accepting a proof.
- **[NX-KM-§3.2.15]** Verifiers **MUST** enforce the Verifier Acceptance Policy (Section 2.2.1) deterministically, including key validity and revocation checks.

---

## 4. Key Lifecycle Requirements (Frozen)

### 4.1 Generation

- **[NX-KM-§4.1.1]** All key generation **MUST** use OS CSPRNG.
- **[NX-KM-§4.1.2]** Domain-separated derivations **MUST** use HKDF with explicit labels (no ambiguous derivations).
- **[NX-KM-§4.1.3]** Keys **MUST** be scoped to their minimum purpose; cross-purpose reuse is forbidden.

### 4.2 Storage

- **[NX-KM-§4.2.1]** RS and other high-value subject secrets **MUST** be stored in secure storage when available (secure enclave/keystore/TPM-class storage) or encrypted at rest under a locally held key.
- **[NX-KM-§4.2.2]** Plaintext private keys **MUST NOT** be written to disk.
- **[NX-KM-§4.2.3]** Secrets in memory **SHOULD** be minimized in lifetime and **SHOULD** be zeroed after use where feasible.

### 4.3 Use

- **[NX-KM-§4.3.1]** Private-key operations **MUST** be constant-time where applicable.
- **[NX-KM-§4.3.2]** Identity-critical signing and proof generation **MUST** require explicit subject authorization (local policy).
- **[NX-KM-§4.3.3]** Services **MUST** enforce least-privilege access tokens for K8/K9/K10/K11.

### 4.4 Rotation

- **[NX-KM-§4.4.1]** Rotation **MUST** be supported for all key classes.
- **[NX-KM-§4.4.2]** Rotation **MUST** be mandatory after suspected compromise.
- **[NX-KM-§4.4.3]** Rotation **MUST** not introduce cross-context or cross-time linkability for identity proofs.

### 4.5 Revocation

- **[NX-KM-§4.5.1]** Issuer keys **MUST** have a revocation mechanism that verifiers can check.
- **[NX-KM-§4.5.2]** Revocation checks **MUST** not require stable identifiers about subjects.

### 4.6 Destruction

- **[NX-KM-§4.6.1]** When a key is destroyed, implementations **MUST** remove it from storage and invalidate its usage paths.
- **[NX-KM-§4.6.2]** Destruction **MUST** be irreversible at the application layer (no “undo”).

---

## 5. Subject Backup & Recovery (Non-Discretionary)

> NYX will not “save” the subject. Recovery is a protocol mechanism, not a human process.

### 5.1 Backup

- **[NX-KM-§5.1.1]** RS backups **MUST** be encrypted under a subject-controlled secret.
- **[NX-KM-§5.1.2]** Backups **MUST NOT** be stored in plaintext, screenshots, notes apps, email drafts, or chat logs.
- **[NX-KM-§5.1.3]** If split-backup schemes are used (e.g., secret sharing), shares **MUST** not be stored in the same trust domain.

### 5.2 Recovery

- **[NX-KM-§5.2.1]** Recovery **MUST** be protocol-defined and non-discretionary.
- **[NX-KM-§5.2.2]** Recovery **MUST NOT** require administrator approval, manual support intervention, or issuer permission.
- **[NX-KM-§5.2.3]** Recovery **MUST** produce new cryptographic material and explicitly retire prior material.

---

## 6. System Key Controls (Insider-Hostile)

### 6.1 Quorum & Separation-of-Duties

- **[NX-KM-§6.1.1]** REL-SIGN (K10) and any key that can change production code/config **MUST** be protected by a quorum policy (M-of-N) with **independent custodians**.
- **[NX-KM-§6.1.1a]** Such keys **MUST** be non-exportable in normal operation (hardware-backed or equivalently isolated) and **SHOULD** be kept offline except during signing ceremonies.
- **[NX-KM-§6.1.1b]** The quorum policy **MUST** prevent a single insider from producing a valid release/config signature.
- **[NX-KM-§6.1.2]** No single operator account **MAY** both (a) approve a release and (b) deploy it to production.
- **[NX-KM-§6.1.3]** Production access **MUST** be time-bounded and auditable; standing privileges are discouraged.
- **[NX-KM-§6.1.4]** Any “break-glass” mechanism **MUST NOT** be implemented as a single privileged key. Break-glass, if present, **MUST** be procedural (quorum + logged + time-bounded) and **MUST** preserve constitutional constraints (no discretionary identity takeover).

### 6.2 Key Scope & Blast Radius

- **[NX-KM-§6.2.1]** Service keys (K8/K9) **MUST** be scoped to a single environment and service.
- **[NX-KM-§6.2.2]** Cross-environment key reuse is **forbidden** (dev/staging/prod separation).
- **[NX-KM-§6.2.3]** Key compromise **MUST** have a defined containment action (rotate + invalidate + attest).

### 6.3 Attestation & Integrity

- **[NX-KM-§6.3.1]** Deployed artifacts and configuration **MUST** be verifiable via signature (REL-SIGN/CFG-SIGN).
- **[NX-KM-§6.3.2]** Systems **MUST** reject unsigned or unknown-signature artifacts.

### 6.4 KMS/HSM Characteristics (Vendor-Neutral)

- **[NX-KM-§6.4.1]** System keys stored in managed services (e.g., KMS/HSM-class systems) **MUST** be non-exportable and access-controlled by least privilege.
- **[NX-KM-§6.4.2]** Access to system keys **MUST** use short-lived credentials and **MUST** be bound to an authenticated workload identity (not a human static secret).
- **[NX-KM-§6.4.3]** Any key use **MUST** be auditable with tamper-evident logs.
- **[NX-KM-§6.4.4]** System key access policies **MUST** support emergency lock-down without granting discretionary decryption of subject content.

---

## 7. Logging & Audit (Without Leaking)

- **[NX-KM-§7.0.1]** Key events **MUST** be auditable as events: generate, rotate, revoke, deploy, destroy.
- **[NX-KM-§7.0.2]** Audit logs **MUST NOT** contain secret material.
- **[NX-KM-§7.0.3]** Audit logs **SHOULD** be tamper-evident (append-only + integrity checks).

### 7.1 Key Transparency (High-Value Keys)

- **[NX-KM-§7.1.1]** High-value key events (K10/K11, and issuer key rotations) **MUST** be recorded in an append-only, tamper-evident transparency log.
- **[NX-KM-§7.1.2]** The transparency log **MUST** be independently verifiable (integrity proofs) and **MUST NOT** contain secret material.
- **[NX-KM-§7.1.3]** Verifiers and deployments **SHOULD** be able to check whether a given issuer key or release key is current, rotated, or revoked using the transparency record.

---

## 8. Incident Response (Key Compromise Playbooks)

### 8.1 Severity Classes

- **SEV-0:** Subject RS compromise suspected/confirmed.
- **SEV-1:** Issuer signing key compromise suspected/confirmed.
- **SEV-2:** NYX service key compromise (K8/K9) suspected/confirmed.
- **SEV-3:** Release/config signing key compromise (K10/K11) suspected/confirmed.

### 8.2 Mandatory Actions

- **[NX-KM-§8.2.1]** Compromised keys **MUST** be invalidated and rotated immediately.
- **[NX-KM-§8.2.2]** For SEV-3, deployments **MUST** halt until the release chain of trust is re-established.
- **[NX-KM-§8.2.3]** Issuer compromises **MUST** trigger revocation publication and verifier update guidance.
- **[NX-KM-§8.2.4]** Subject compromises **MUST** trigger protocol-defined recovery/rotation flows; no manual “account restore.”
- **[NX-KM-§8.2.5]** For SEV-1 (issuer key compromise), verifiers **MUST** have a deterministic rule to reject revoked issuer keys without requiring subject identifiers.
- **[NX-KM-§8.2.6]** For SEV-2 (service key compromise), all affected service identities **MUST** be rotated and prior credentials **MUST** be invalidated; deployments **MUST** re-attest integrity.
- **[NX-KM-§8.2.7]** For SEV-0 (subject RS compromise), any lineage/rotation mechanism **MUST** preserve unlinkability guarantees and **MUST NOT** introduce cross-context identifiers.

---

## 9. Exceptions & Change Control

- **[NX-KM-§9.0.1]** Exceptions to this model are forbidden by default.
- **[NX-KM-§9.0.2]** Any exception proposal **MUST** include: threat-model justification, blast-radius analysis, and explicit rollback.
- **[NX-KM-§9.0.3]** Any approved exception **MUST** be versioned as a document change.

---

## 10. Freeze Boundary

The following are frozen for **Key_Management_Model v1**:

1) Invariants in Section 1
2) Key taxonomy in Section 2
3) Responsibility model in Section 3
4) Lifecycle requirements in Section 4
5) Non-discretionary backup/recovery rules in Section 5
6) Quorum and separation-of-duties in Section 6

Any change requires a version bump and an explicit threat-model justification.

---

## 11. Compliance Checklist (v1)

An implementation is compliant if and only if:

- User RS never leaves the subject trust boundary
- NYX services cannot decrypt subject-protected content
- No single operator key can change code/config without quorum
- Issuer sets and acceptance rules are explicit, versioned, and auditable (including risk classification)
- High-risk claims default to diversified issuance (recommended 2-of-3) unless explicitly degraded
- Verifiers deterministically enforce key validity + revocation without subject identifiers
- All key classes can rotate and be revoked
- Logs capture key events but never secrets (and high-value key events are transparency-logged)
- Recovery is protocol-defined, not human-discretionary

---

*End of Key_Management_Model*

