# Q9 Testnet Alpha Release Window

## Purpose
Define the Q9 release window policy and the allowed actions during the window.

## Scope
Testnet Alpha only. Documentation, evidence, and zero-semantic patches.

## Non-Scope
No protocol semantic changes. No mainnet claims. No new runtime features.

## Release Window Rules
- Changes MUST be documentation-only or zero-semantic patches with regression evidence.
- Evidence artifacts MUST remain deterministic and verifiable.
- UI and backend copy MUST remain Testnet Alpha labeled.
- Any change that affects determinism or evidence format is NOT allowed.

## Verification
- python -m compileall packages/l0-identity/src
- python scripts/nyx_run_all_unittests.py
- PYTHONPATH="packages/conformance-v1/src" python -m conformance_v1.runner --out nyx_conformance_report.json

## Freeze / Change Control
- Q1–Q8 semantics remain sealed.
- Q9 release window allows only documentation and zero-semantic changes.
