# Crypto\_Stack\_Selection\_v1

Version: v1
Status: Draft (Target: Q1 Freeze)
Owner: NYX Core
Date: 2026-02-01
Last-Modified: 2026-02-01
Related: NYX_Constitution_v1_draft.md; Threat_Model_v1.md; NYX_ZK-ID_Spec_v1.md; NYX_Web2_Gateway_Principles.md

---

## Normative Language

The key words **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** in this document are to be interpreted as described in RFC 2119.

Each normative requirement is assigned a stable identifier in the form **[NX-CS-§X.Y.Z]**.

---

## Executive Statement

NYX does not win by “the fanciest algorithm.”
NYX wins by **boring, battle-tested primitives** + **hard boundaries** + **zero human trust**.

This document freezes:

- the **cryptographic primitive families** NYX is allowed to use,
- the **default choices** for each family,
- the **constraints** any future change must satisfy.

NYX **MUST NOT** implement custom cryptographic primitives.

---

## 0. Scope

### 0.1 In Scope

This document freezes the baseline crypto stack for:

- Transport security (NYX ↔ infrastructure)
- End-to-end encryption (Subject ↔ Subject, or Subject ↔ Verifier where applicable)
- Digital signatures (application-layer + chain-layer compatibility boundary)
- Zero-knowledge proofs (ZK-ID and future proof-bearing protocol paths)
- Key derivation, hashing, and commitments as required by the above

### 0.2 Out of Scope

- Concrete key custody and operational procedures (see `Key_Management_Model.md`)
- Chain/L2 final selection and its transaction signature scheme (frozen later in architecture)
- Any feature intended to bypass external anti-abuse systems

---

## 1. Non-Negotiable Constraints (Constitutional)

### 1.1 No Self-Made Crypto

- **[NX-CS-§1.1.1]** NYX **MUST NOT** design or implement new cryptographic primitives.
- **[NX-CS-§1.1.2]** NYX **MUST** use widely deployed, publicly reviewed primitives, with mature reference implementations.
- **[NX-CS-§1.1.3]** NYX **MUST NOT** introduce custom protocol variants of standard primitives (e.g., custom nonce schemes, non-standard signature encodings, ad-hoc KDF parameter sets, or “slightly modified” constructions) unless explicitly specified in this document and justified by the threat model.

### 1.2 No Human Trust Assumptions

- **[NX-CS-§1.2.1]** NYX **MUST NOT** require a trusted operator, administrator, or “security team key” to preserve core guarantees.
- **[NX-CS-§1.2.2]** If a component can be compromised by a single insider key, it is **non-compliant** by default.

### 1.3 Wallet ≠ Identity

- **[NX-CS-§1.3.1]** Wallet keys **MUST NOT** be treated as NYX identity roots.
- **[NX-CS-§1.3.2]** Identity cryptography **MUST** support rotation and context separation by construction.

### 1.4 Metadata Is Hostile

- **[NX-CS-§1.4.1]** The crypto stack **MUST** assume network and platform metadata correlation is always attempted.
- **[NX-CS-§1.4.2]** “Privacy by policy” is invalid; only cryptography + structure count.

---

## 2. Decision Principles

### 2.1 Baseline Principles

- **[NX-CS-§2.1.1]** Prefer primitives with broad real-world deployment and multiple independent implementations.
- **[NX-CS-§2.1.2]** Prefer primitives that reduce catastrophic failure modes (e.g., avoid fragile constructions where a single misuse breaks everything).
- **[NX-CS-§2.1.3]** Prefer primitives friendly to constant-time implementations.
- **[NX-CS-§2.1.4]** Prefer primitives that minimize foot-guns (safe defaults > flexible knobs).

### 2.2 Compatibility Principles

- **[NX-CS-§2.2.1]** NYX **MUST** maintain a clean separation between:
  - **Application / identity crypto** (NYX-native)
  - **Chain transaction crypto** (environment-dependent)
- **[NX-CS-§2.2.2]** Chain-level signatures are treated as **transport/auth to the chain**, not as identity.

---

## 3. Baseline Primitive Set (Frozen)

> **Policy:** A primitive is either **Selected**, **Allowed (fallback)**, or **Forbidden**.

### 3.1 Randomness

- **Selected:** OS-provided CSPRNG only (platform secure RNG APIs)
- **[NX-CS-§3.1.1]** All key material generation **MUST** use OS CSPRNG.
- **[NX-CS-§3.1.2]** Web / JS environments **MUST** use `WebCrypto.getRandomValues` (or platform-equivalent secure RNG).
- **[NX-CS-§3.1.3]** Mobile and desktop native clients **MUST** use the operating system’s secure RNG APIs (and where available, secure hardware-backed sources).
- **[NX-CS-§3.1.4]** Implementations **MUST NOT** derive entropy from timestamps, device identifiers, network data, chain data, or any other low-entropy/observable sources.
- **Forbidden:** custom PRNGs, deterministic keygen without proven design

### 3.2 Hash Functions

- **Selected (general-purpose):** SHA-256

- **Allowed (compatibility):** SHA-512/256, Keccak-256 (only where chain compatibility forces it)

- **Selected (in-circuit / ZK-friendly):** Poseidon (only inside ZK circuits)

- **[NX-CS-§3.2.1]** Public commitments intended to be verified on common chains **SHOULD** use the chain’s standard hash when required by the verifier environment.

- **[NX-CS-§3.2.2]** Inside ZK circuits, hash choice **MUST** prioritize proof efficiency while preserving security assumptions (Poseidon class).

### 3.3 Key Derivation (KDF)

- **Selected:** HKDF-SHA-256
- **[NX-CS-§3.3.1]** All domain-separated key derivations **MUST** use HKDF with explicit info labels.

### 3.4 Symmetric Encryption (AEAD)

- **Selected:** XChaCha20-Poly1305

- **Allowed (hardware acceleration / compliance):** AES-256-GCM

- **[NX-CS-§3.4.1]** All message encryption **MUST** be AEAD.

- **[NX-CS-§3.4.2]** Nonce management **MUST** be misuse-resistant by default (XChaCha preferred).
- **[NX-CS-§3.4.3]** AEAD usage **MUST** bind protocol context via Associated Data (AAD). At minimum, AAD **MUST** include: `protocol_version`, `context_id`, `message_type`, and `direction` (sender→receiver).
- **[NX-CS-§3.4.4]** Implementations **MUST NOT** reuse a `(key, nonce)` pair. Any design that risks nonce reuse **MUST** prefer extended-nonce schemes (e.g., XChaCha) and explicit uniqueness rules.

- **Forbidden:** CBC-mode, ECB-mode, raw stream ciphers without authentication

### 3.5 Key Exchange / Forward Secrecy

- **Selected:** X25519 (ECDH)

- **Selected (transport):** TLS 1.3 with (EC)DHE

- **[NX-CS-§3.5.1]** Any interactive secure channel **MUST** provide forward secrecy.

- **[NX-CS-§3.5.2]** Any long-term static key compromise **MUST NOT** reveal past session content.

### 3.6 Transport Security

- **Selected:** TLS 1.3

- **[NX-CS-§3.6.1]** All NYX service-to-service and client-to-gateway traffic **MUST** be protected by TLS 1.3 or an equivalent channel with FS.

- **[NX-CS-§3.6.2]** TLS downgrade paths **MUST** be disabled.
- **[NX-CS-§3.6.3]** Implementations **MUST** disable TLS 1.2 and below.
- **[NX-CS-§3.6.4]** Implementations **MUST** forbid static key exchange (e.g., static RSA) and **MUST** require (EC)DHE for forward secrecy.
- **[NX-CS-§3.6.5]** Implementations **MUST** restrict TLS cipher suites to AEAD-only.
- **[NX-CS-§3.6.6]** TLS 0-RTT **MUST** be disabled by default.
- **[NX-CS-§3.6.6a]** If TLS 0-RTT is enabled for a specific service, it **MUST** be restricted to **idempotent, read-only** requests (no protocol state mutation, no value transfer, no authorization changes).
- **[NX-CS-§3.6.6b]** Any 0-RTT-enabled endpoint **MUST** implement explicit replay protection (server-side anti-replay) and **MUST** be accompanied by a threat-model justification documented per deployment.
- **[NX-CS-§3.6.7]** Certificate validation **MUST** be enforced (chain validation + hostname validation). Any exception (e.g., pinned certs in constrained environments) **MUST** be explicitly documented per deployment.

### 3.7 Application / Identity Signatures

- **Selected:** Ed25519

- **Allowed (where needed):** secp256k1 (compat), P-256 (only for strict platform constraints)

- **[NX-CS-§3.7.1]** NYX identity-level signing **MUST** be independent of chain transaction keys.

- **[NX-CS-§3.7.2]** Identity signing **MUST** support rotation without global identifiers.
- **[NX-CS-§3.7.3]** All signatures **MUST** be domain-separated. Signed payloads **MUST** include an unambiguous domain tag, at minimum: `"NYX:Identity:v1"`, plus `protocol_version`, `context_id`, and `message_type`.
- **[NX-CS-§3.7.4]** All signed structures **MUST** use canonical serialization (one unique encoding per semantic message). Multiple encodings for the same semantic message are **forbidden**.
- **[NX-CS-§3.7.5]** Implementations **MUST NOT** accept signatures over partially specified payloads (no implicit defaults). Every field affecting meaning **MUST** be explicitly present in the signed bytes.

### 3.8 Chain Transaction Signatures (Boundary)

- **Frozen Boundary:** Chain-level transaction signature scheme is **environment-defined** and **MUST NOT** be used as identity.

- **[NX-CS-§3.8.1]** Chain transaction keys **MAY** be secp256k1 (EVM) or other chain-required schemes, but are treated strictly as transaction authorization.

- **[NX-CS-§3.8.2]** No protocol rule **MAY** bind reputation, credit, or identity to a chain address.

### 3.9 Zero-Knowledge Proof Stack (ZK-ID Baseline)

NYX ZK must satisfy:

- context binding
- domain separation
- unlinkability by construction
- no trusted operator authority

**Selected (v1 baseline):**

- **Proof system class:** SNARK/STARK family with mature tooling
- **Setup policy:** **Transparent setup preferred**; if a trusted setup is used, it MUST be universal, multi-party, publicly verifiable, and MUST NOT introduce any privileged recovery/override path.

**Frozen Requirements:**

- **[NX-CS-§3.9.1]** Proofs **MUST** be context-bound and non-replayable across contexts.
- **[NX-CS-§3.9.2]** Proof outputs **MUST NOT** become stable identifiers.
- **[NX-CS-§3.9.3]** ZK selection **MUST** keep verifier assumptions compatible with the Week 3 ZK-ID invariants.

**Open Item (explicit):** The specific proving system and curve selection is deferred to the architecture freeze, because verifier environment (L1/L2 choice) can hard-lock these constraints.

**Proof Envelope (frozen minimum):**
- **[NX-CS-§3.9.4]** Every proof submission **MUST** include `protocol_version`, `context_id`, `statement_id`, and a freshness value (`nonce` or `epoch`).
- **[NX-CS-§3.9.5]** Proofs **MUST** be non-replayable across contexts. Any replay-prevention tag/nullifier **MUST** be domain-separated by `context_id`.
- **[NX-CS-§3.9.6]** Proof outputs **MUST NOT** contain stable identifiers, long-lived tags, or reusable correlation material.
- **[NX-CS-§3.9.7]** If nullifiers are used (e.g., to prevent double-use), they **MUST** be scoped to a single context and **MUST NOT** be linkable across contexts or time beyond that scope.

### 3.10 Commitments & Merkle Structures

- **Selected (general commitments):** Hash-based commitments using SHA-256
- **Selected (ZK commitments / Merkle inside circuits):** Poseidon-based commitments/trees
- **Allowed (compat):** Keccak-based Merkle for EVM verifier constraints

---

## 4. Library & Implementation Policy (Frozen)

### 4.1 Dependency Selection Rules

- **[NX-CS-§4.1.0]** Crypto dependencies are part of the security boundary; supply-chain integrity is mandatory.
- **[NX-CS-§4.1.1]** NYX crypto implementations **MUST** use well-maintained, widely reviewed libraries.
- **[NX-CS-§4.1.2]** All crypto dependencies **MUST** be version-pinned.
- **[NX-CS-§4.1.3]** Builds **SHOULD** be reproducible where feasible.
- **[NX-CS-§4.1.4]** Any dependency requiring unsafe language bindings **MUST** have isolation boundaries and fuzzing coverage.
- **[NX-CS-§4.1.5]** A Software Bill of Materials (SBOM) **MUST** be produced for every release/build artifact that includes cryptographic code.
- **[NX-CS-§4.1.6]** Implementations **MUST** include Known-Answer Tests (KAT) for every selected primitive and for all custom protocol encodings/serializations.
- **[NX-CS-§4.1.7]** Parsers, decoders, and proof/signature verification boundaries **SHOULD** be fuzz-tested; where FFI/unsafe code exists, fuzzing is **mandatory**.
- **[NX-CS-§4.1.8]** Unsafe/FFI crypto components **MUST** be isolated behind a narrow interface; when feasible they **SHOULD** be sandboxed (process isolation) to reduce blast radius.

### 4.2 Constant-Time & Side-Channel Hygiene

- **[NX-CS-§4.2.1]** Private-key operations **MUST** use constant-time implementations.
- **[NX-CS-§4.2.2]** Secrets **MUST NOT** be logged, serialized in plaintext, or exposed to crash dumps.

---

## 5. Forbidden List (Hard No)

- **[NX-CS-§5.0.1]** Home-grown encryption, signatures, ZK constructions
- **[NX-CS-§5.0.2]** “Encrypt-then-hope” (no authentication)
- **[NX-CS-§5.0.3]** Deterministic nonces without proven safe construction
- **[NX-CS-§5.0.4]** Any design where a single admin key can silently change security guarantees

---

## 6. Freeze Boundary

The following are frozen for **Crypto\_Stack\_Selection\_v1**:

1. Primitive families and defaults in Section 3
2. “No self-made crypto” policy
3. Wallet–Identity separation boundary
4. Implementation policy in Section 4
5. Forbidden list in Section 5

Any change to frozen items requires:

- a new minor/major version of this document, and
- an explicit threat-model justification.

---

## 7. Open Items (Explicitly Allowed)

These are intentionally deferred but constrained:

1. **ZK proving system + curve + verifier environment** (must satisfy Section 3.9 requirements)
2. **Chain transaction signature scheme** (must satisfy Section 3.8 boundary)
3. **Optional post-quantum readiness** (research track only; not v1 baseline)

### 7.1 Deprecation & Upgrade Process (Frozen)

- **[NX-CS-§7.1.1]** Any change to **Selected / Allowed / Forbidden** primitives **MUST** trigger a version bump of this document and an explicit changelog entry.
- **[NX-CS-§7.1.2]** Any proposed change **MUST** include: threat-model justification, migration plan, compatibility window (or explicit break), and rollback strategy.
- **[NX-CS-§7.1.3]** Silent changes are forbidden. Implementations **MUST NOT** swap primitives, parameters, encodings, or verifier assumptions without an explicit document update.
- **[NX-CS-§7.1.4]** This document **MUST** maintain a `Deprecated` list (with deprecation date and removal target) to prevent permanent “allowed forever” creep.

---

## 8. Compliance Checklist (v1)

An implementation is compliant with this selection freeze if and only if:

- It uses only Selected/Allowed primitives
- It never treats wallet/addresses as identity
- It enforces AEAD + forward secrecy for channels
- It keeps ZK proofs context-bound and non-identifying
- It introduces no privileged override keys

---

*End of Crypto\_Stack\_Selection\_v1*

