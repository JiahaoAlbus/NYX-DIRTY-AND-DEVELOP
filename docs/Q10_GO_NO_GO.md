# Q10 Go / No-Go (Testnet Beta RC)

## Purpose
Define objective, verifiable criteria for Testnet Beta RC readiness.

## Scope
Applies to Q10 Testnet Beta only.

## Non-Scope
- Mainnet launch authorization.
- External audits or legal sign-off.

## Go Criteria (All MUST be satisfied)
1) Canonical verification commands complete successfully.
2) Total tests are non-zero and all pass.
3) Conformance runner completes successfully with no failed rules.
4) Evidence exports are deterministic for fixed inputs.
5) No banned copy claims appear in UI or docs.
6) Treasury routing is configured for testnet (env provided) or explicitly marked as dry mode.

## No-Go Criteria (Any single item is sufficient)
- Any failing verification or conformance check.
- Evidence fields missing or reordered relative to the immutable contract.
- Protocol fee bypass observed for a value-moving action.
- Path traversal or unsafe file access detected.

## Evidence / Verification
Use the canonical command set in the Q10 audit reproduction documentation.

## Freeze / Change Control
Any change after RC MUST be additive or a zero-semantic patch with regression evidence.
