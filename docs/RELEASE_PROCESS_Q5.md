# Q5 Release Process

## Purpose
Define release gating and evidence collection for Q5.

## Scope
- Router v1 and reference client v1.
- Deterministic evidence collection.

## Non-Scope
- Production bridge or on/off implementation.
- External deployment automation.

## MUST
- Full test suite MUST be green before any release.
- PROPERTY_N value MUST be recorded.
- Determinism outputs MUST match for identical inputs.

## MUST NOT
- Do not bypass receipts or replay verification.
- Do not change sealed semantics without new versioning.

## Evidence / Verification
```
python -m compileall packages/l0-identity/src
python -m unittest discover -s packages/l0-identity/test -p "*_test.py" -v
```

Conformance report:
```
PYTHONPATH="packages/conformance-v1/src" python -m conformance_v1.runner --out /tmp/nyx_conformance_report.json
```

## Freeze & Change Control
- Changes follow `docs/CHANGE_CONTROL.md`.
