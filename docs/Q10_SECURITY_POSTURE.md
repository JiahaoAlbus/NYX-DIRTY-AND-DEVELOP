## Purpose
- Record Q10 Testnet Beta security posture, attack surface, and hardening requirements.

## Scope
- Backend gateway validation and safe file handling.
- Deterministic evidence export and replay verification.
- Adversarial tests for tamper, bounds, and invalid input handling.

## Non-Scope
- Mainnet security claims or guarantees.
- External threat intelligence feeds.

## Normative Rules (MUST / MUST NOT)
- All public inputs MUST be validated and bounded.
- All file access MUST use allowlists and safe path resolution.
- Error messages MUST be deterministic and MUST NOT leak secrets.
- Evidence export MUST remain deterministic and replayable.
- Economic actions MUST preserve protocol fee > 0 and additive platform fees.

## Evidence and Verification
- The canonical test runner MUST pass with non-zero total tests.
- Conformance report MUST be generated and indicate ok.
- Adversarial tests MUST cover invalid identifiers and tampered evidence.

## Freeze and Change Control
- This posture is normative for Q10 Testnet Beta.
- Changes MUST be additive and MUST NOT alter evidence outputs.
