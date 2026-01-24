# Q9 Backend API Contract (Testnet Alpha)

Purpose
- Define the text contract for the Q9 backend gateway API.

Scope
- Request/response fields for deterministic evidence runs.

Non-Scope
- No protocol semantics changes.
- No authentication or identity features.

Definitions
- Evidence fields MUST match the Q7 evidence contract exactly.
- All outputs MUST be deterministic for the same inputs.

Endpoints (text contract)
- POST /run
  - Request fields: seed (int), run_id (string), module (string), action (string), payload (object)
  - Response fields: run_id (string), status (string), replay_ok (bool)
- GET /status
  - Query: run_id
  - Response: status, replay_ok, error (if failed)
- GET /evidence
  - Query: run_id
  - Response: protocol_anchor, inputs, outputs, receipt_hashes, state_hash, replay_ok, stdout
- GET /artifact
  - Query: run_id, name
  - Response: raw bytes
- GET /export.zip
  - Query: run_id
  - Response: deterministic zip bytes
- GET /list
  - Response: list of run_id + status

Rules
- run_id MUST be provided and MUST pass allowlist validation.
- payload size MUST be bounded.
- Artifact name MUST be from a fixed allowlist.
- Evidence fields MUST be emitted verbatim from backend evidence generator.

Evidence/Verification
- Run the canonical test runner and conformance runner for evidence export behavior.

Change Control
- Any contract change MUST be additive and versioned.
