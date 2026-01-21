# Ecosystem Modules Stubs (Interfaces Only)

Purpose
- Define interface boundaries for ecosystem modules without implementing runtime logic.

Scope
- Marketplace, chat, and entertainment module interfaces.
- Platform fee hook extension point usage.

Non-Scope
- No runtime implementations.
- No UI behavior or client workflows.
- No changes to sealed protocol semantics.

Definitions
- Module boundary: a strict interface between core protocol and ecosystem features.
- Evidence ref: a pointer to a deterministic evidence bundle.

Normative Rules
- Ecosystem modules MUST NOT modify core protocol state directly.
- Ecosystem modules MUST use the platform fee hook for additive fees.
- Ecosystem modules MUST export evidence references only.
- Ecosystem modules MUST remain detached from core kernel internals.

Security and Abuse Boundaries
- Modules MUST NOT embed secrets or sensitive material in outputs.
- Modules MUST NOT claim live network status or operational metrics.

Evidence and Enforcement
- Interface-only packages MUST be importable without runtime side effects.
- Guard tests MUST fail if ecosystem stubs import sealed core packages.

Freeze and Change Control
- This document is normative for interface boundaries.
- Changes require a versioned update and regression evidence.
