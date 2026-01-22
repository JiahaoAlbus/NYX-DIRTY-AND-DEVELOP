# Q8 Audit Pack

Purpose
- Provide auditor-ready, reproducible evidence for the Q8 ecosystem layer.

Scope
- Web portal and backend gateway integration.
- Deterministic evidence generation and export.
- Conformance drills for UI, gateway, and platform fee hook.

Non-Scope
- Protocol semantics or fee model changes.
- Production on/off ramp or bridge execution.

MUST and MUST NOT Rules
- Evidence outputs MUST use the v1 contract and remain deterministic for identical inputs.
- Platform fee MUST remain additive and MUST NOT replace the protocol fee.
- UI and backend MUST NOT introduce identity, account, or wallet semantics.
- No live operational claims are permitted in UI or docs.

Evidence and Verification
- Canonical verification commands are defined in Q8 audit repro commands.
- Conformance runner MUST pass with all drills.
- One-shot repro script MUST produce evidence bundles for exchange, chat, marketplace, and entertainment.

Freeze and Change Control
- Q8 is additive only. Any semantic change requires a new version and regression evidence.
