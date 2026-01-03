# Engineering Guidelines (NYX) — v1.0 (Week 12 Deliverable)

**Status:** Draft (Q2 Dev-Prep)  
**Authority:** Subordinate to Q1 Frozen Set (NYX_Q1_Frozen_List) and all listed normative sources.  
**Rule:** If this document conflicts with any higher-authority frozen rule, this document is wrong.

---

## 0. Non‑Negotiables (Read Before Writing Code)

NYX engineering is not “build fast.” It is **build so it cannot quietly become evil**.

### 0.1 Constitutional invariants we must never violate
These are treated as **compile-time constraints** on every PR:

- Wallet ≠ identity (no identity derived from wallet address / account / keypair).
- No trusted admins / discretionary recovery / support override.
- **No free shared-state actions** (no fee bypass lanes, no privileged exemptions).
- Context separation + unlinkability by construction (no stable identifiers across contexts/time).
- Web2 is hostile input; Web2 access must be mediated by Gateway, and **Gateway must not bypass anti-abuse / regulatory controls**.
- One-way dependency law (L0→L1→L2→L3→L4, no back-propagation).

**Compliance stance:** If a PR introduces ambiguity, interpret it as: **more restriction, more auditability, less privilege**.

---

## 1. Repository Setup (Mono‑repo, Layered)

### 1.1 Top-level layout (recommended)
```
nyx/
  docs/                      # normative + engineering docs (versioned)
  specs/                     # frozen specs mirror (read-only copies + links)
  packages/
    l0-identity/             # ZK-ID interfaces, context separation, lifecycle ops
    l1-chain/                # chain adapter interfaces (environment-defined)
    l2-economics/            # fee components, accounting traces, receipts
    l3-markets/              # (Q2: stubs only unless explicitly scoped)
    l4-gateway/              # Web2 gateway skeleton (no bypass behaviors)
    sdk/                     # developer-facing SDK, no UI
  tooling/
    scripts/                 # reproducible tooling (lint, format, sbom)
    ci/                      # CI helpers
  .github/                   # workflows, templates
```

### 1.2 Module boundaries (hard rule)
- Each layer is a **package** with explicit public interfaces.
- Higher layers may import lower layers only.
- No cross-package “utility dumping ground.” If it touches invariants, it lives in the layer that owns the invariant.

### 1.3 Language + runtime (practical defaults)
- Prefer **one** primary implementation language for core packages in Q2 to reduce supply-chain and audit surface.
- Cryptography MUST use approved libraries; never “quick implementations.”

(Concrete language choice is an implementation decision; keep it consistent and minimize surface.)

---

## 2. Development Workflow (Make It Boring)

### 2.1 Branch strategy
- `main`: always releasable, protected.
- `develop` (optional): only if release cadence requires it; otherwise, trunk-based.
- Feature branches: `feat/<scope>-<short-desc>`, `fix/<...>`, `chore/<...>`.

### 2.2 Pull Request policy (required)
A PR is mergeable only if all are true:
- CI green (build, test, lint, typecheck).
- **Conformance tests green** (Section 6).
- Security checks green (SAST/dependency scan).
- No TODOs that hide security decisions (TODOs allowed only with explicit issue link + owner + deadline).
- Review: minimum 1 reviewer (2 if touching cryptography, fee logic, identity invariants, or governance).

### 2.3 Commit conventions (recommended)
Use Conventional Commits:
- `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`
- Include scope: `feat(l0): ...`
- Breaking changes must be explicit.

---

## 3. CI/CD Baseline (GitHub Actions suggested)

### 3.1 Required CI jobs
1. **Build** (pinned toolchain)
2. **Unit tests**
3. **Property / fuzz tests** (for parsers, decoders, verification boundaries)
4. **Lint + formatting**
5. **Static analysis** (SAST)
6. **Dependency / SBOM** generation
7. **Conformance suite** (NYX invariants)
8. **Artifact signing** (release candidates only)

### 3.2 Supply chain hardening (required)
- Dependencies **version-pinned**.
- Lockfiles committed.
- Build must be reproducible where feasible.
- Generate SBOM for release artifacts.
- No unsigned artifacts allowed for deployment.

---

## 4. Security Engineering Rules (No “Later”)

### 4.1 Secrets handling (hard)
- Secrets MUST NOT be logged.
- No private keys / root secrets / recovery material in telemetry, crash dumps, or test fixtures.
- Use env-based secrets in CI; never commit secrets.

### 4.2 Cryptography rules (hard)
- No self-made crypto.
- AEAD only for encryption.
- Forward secrecy for interactive channels.
- Domain separation in every signature/proof payload.
- Canonical serialization required (no multiple encodings for same semantic message).

### 4.3 Key management (hard)
- User Root Secret never leaves client trust boundary.
- Service keys are replaceable; no forever keys.
- Release/signing keys require quorum custody.

---

## 5. Testing Strategy (Designed for Adversaries)

### 5.1 Test types (required)
- **Unit**: pure logic.
- **Integration**: cross-package contracts (L0↔L2, etc.).
- **Property**: invariants (e.g., context separation, non-negativity of fee vectors).
- **Fuzz**: all boundary parsers/decoders and proof/tx verification surfaces.
- **Conformance**: “NYX must not become invalid.”

### 5.2 Test data rules
- Never use real keys.
- Deterministic fixtures must not leak stable identifiers across contexts unless explicitly required by spec (rare).

---

## 6. NYX Conformance Suite (Gatekeeper)

### 6.1 What this is
A mandatory test suite that encodes Q1 frozen invariants as executable checks. If it fails, the PR is non-compliant.

### 6.2 Minimum v1 conformance checks (must exist in Q2)
- **No wallet-as-identity**: no API accepts wallet address/account as identity root/identifier.
- **No free lane**: all shared-state mutations require non-zero fee; sponsored transactions pay identical fee vectors.
- **No privileged bypass**: no “admin allowlist” for fees, inclusion, execution, or identity.
- **Context separation**: proofs/tags/nullifiers cannot be reused across contexts.
- **No stable identifiers across contexts/time**: data model forbids persistent correlation tokens unless explicitly allowed by L0 spec.
- **Gateway boundaries** (if Gateway touched): cannot bypass external anti-abuse controls; cannot simulate human behavior.

---

## 7. Observability (Auditability Without Leaking)

### 7.1 Logging policy
- Structured logs only.
- Redaction by default.
- No PII assumptions; treat metadata as hostile.

### 7.2 Audit events (required where applicable)
- Fee component breakdown for actions (auditable accounting traces).
- Key lifecycle events (without secrets).
- Release/config signature verification events.

---

## 8. Documentation & Change Control

### 8.1 Docs-as-law
- Specs are the source of truth; code must cite spec section/requirement IDs when implementing invariants.
- Any change touching frozen items is automatically rejected (requires new major protocol version, not a PR).

### 8.2 Versioning
- Engineering Guidelines: semantic versioning.
- Any changes to build security / release signing require a changelog entry.

---

## 9. Definition of Done (NYX Edition)

A feature is “done” only when:
- It compiles.
- It passes tests.
- It passes conformance.
- It is auditable.
- It does not introduce privilege.
- It does not require trusting a human to stay safe.

---

## References (Authority Sources)
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
