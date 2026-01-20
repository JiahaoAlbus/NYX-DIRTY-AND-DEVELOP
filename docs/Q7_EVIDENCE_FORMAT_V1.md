# Q7 Evidence Format v1

## Purpose
Define the single, canonical evidence bundle format used to verify NYX execution deterministically.

## Scope
This format applies to all Q7 reference tooling and any future UI or SDK that emits evidence.

## Non-Scope
- Protocol semantics or fee rules.
- Any cryptographic implementation details.
- Any UI presentation format beyond stdout capture.

## Definitions
- Evidence bundle: a directory containing required files with deterministic content.
- Protocol anchor: the tag and commit that define the exact code baseline.
- Receipt hashes: ordered list of deterministic hashes proving execution and fee enforcement.
- State hash: deterministic post-execution state root (hex).

## Required Files
The evidence bundle MUST contain these files with these exact names:
- protocol_anchor.json
- inputs.json
- outputs.json
- receipt_hashes.json
- state_hash.txt
- replay_ok.txt
- stdout.txt

## Deterministic Ordering Rules
- JSON files MUST be encoded with sorted keys, no extra whitespace, and UTF-8.
- receipt_hashes.json MUST be a JSON array in the exact order defined below.
- stdout.txt MUST contain the exact stdout emitted by the reference CLI.

## Encoding and Hashing Rules
- All hash values MUST be lowercase hex strings.
- state_hash.txt MUST contain a single lowercase hex string with no trailing spaces.
- replay_ok.txt MUST contain either "true" or "false" and a trailing newline.

## Evidence Bundle Contents

### protocol_anchor.json
MUST contain:
- tag: string (e.g., mainnet-1.0)
- commit: string (full SHA)
- describe: string (git describe output)

### inputs.json
MUST contain the deterministic inputs used to generate evidence. At minimum:
- seed: integer

### outputs.json
MUST contain:
- state_hash: string (hex)
- receipt_hashes: array of strings (hex)
- replay_ok: boolean

### receipt_hashes.json
MUST contain a JSON array of receipt hashes in this exact order:
1) fee_receipt_hash
2) tx_hash
3) block_hash

### state_hash.txt
MUST contain the post-execution state hash (hex).

### replay_ok.txt
MUST contain "true" if replay verification succeeded, otherwise "false".

### stdout.txt
MUST contain the raw stdout from the CLI execution.

## Reproducibility Contract
- Same inputs MUST produce identical evidence across machines.
- Evidence MUST NOT include timestamps, environment metadata, or randomness.
- Any non-deterministic output MUST be treated as a failure.

## Security and Abuse Boundaries
- Evidence MUST NOT include secrets, witnesses, or sensitive material.
- Any missing required file MUST be treated as invalid evidence.

## Evidence and Enforcement
- Conformance drills SHOULD validate the evidence bundle structure.
- Determinism guards SHOULD validate byte-for-byte stability of required files.

## Change Control
This format is normative and immutable for Q7. Any change requires a version bump and explicit migration evidence.
