# Q8 Ecosystem Architecture

Purpose
- Define the Q8 ecosystem layer architecture while preserving sealed protocol semantics.

Scope
- Web (NYX Portal), backend gateway, and iOS client surfaces.
- Evidence generation and export using the frozen evidence contract.

Non-Scope
- Protocol logic changes.
- Live network claims or real-world market data.
- Identity or account systems.

Architecture Overview
- Web (NYX Portal): static UI that calls backend endpoints and renders evidence verbatim.
- Backend (Ecosystem Gateway): deterministic wrapper that executes module actions via the evidence generator and exports artifacts.
- iOS Client: mirrors web flows and uses the same backend endpoints.

Evidence Contract Inheritance
- All modules MUST produce the same top-level evidence fields:
  - protocol_anchor
  - inputs
  - outputs
  - receipt_hashes
  - state_hash
  - replay_ok
  - stdout
- Module-specific data MUST be contained within inputs/outputs without changing required fields.

Security Posture
- No identity or account semantics in UI or backend.
- No live operational claims in UI or docs.
- All file access MUST use strict allowlists and safe path resolution.

Evidence and Verification
- Determinism is enforced by fixed seeds and stable serialization.
- Conformance drills MUST fail on missing evidence fields, path traversal, or fee bypass.

Freeze and Change Control
- Architecture boundaries are fixed for Q8.
- Any change to evidence fields requires a versioned update and regression evidence.
