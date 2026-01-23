# Q9 Audit Pack

Purpose
- Provide auditor-ready, reproducible evidence for Q9 Testnet Alpha modules.

Scope
- Exchange, Chat, Marketplace, Entertainment testnet flows.
- Backend gateway evidence export and deterministic replay.
- Additive platform fee routing to the testnet fee vault address.

Non-Scope
- Protocol semantic changes or fee model changes.
- Production on/off ramps or bridge execution.
- Any live market or live social network claims.

MUST and MUST NOT Rules
- Evidence outputs MUST use the v1 evidence contract and remain deterministic for identical inputs.
- Protocol fee MUST remain non-zero for protocol actions; platform fee MUST be additive only.
- UI and backend MUST NOT introduce identity, account, or wallet semantics.
- No live operational claims are permitted in UI or docs.

Evidence and Verification
- Canonical verification commands are defined in Q9 audit repro commands.
- Conformance runner MUST pass with all drills.
- One-shot repro script MUST produce evidence bundles for exchange, chat, marketplace, and entertainment actions.

Freeze and Change Control
- Q9 changes are additive only. Any semantic change requires a new version and regression evidence.
