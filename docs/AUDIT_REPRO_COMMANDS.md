# Audit Repro Commands (Q5)

## Purpose
Provide the single canonical verification command set for Q5.

## Scope
- Full test suite and conformance report generation.

## Non-Scope
- Production deployment steps.

## MUST
- Commands MUST be run on a clean main branch.
- Outputs MUST be recorded with hashes and PROPERTY_N.

## MUST NOT
- Do not modify sources during verification.

## Evidence / Verification
```
python -m compileall packages/l0-identity/src
python -m unittest discover -s packages/l0-identity/test -p "*_test.py" -v
```

Conformance output:
```
PYTHONPATH="packages/conformance-v1/src" python -m conformance_v1.runner --out /tmp/nyx_conformance_report.json
```

## Freeze & Change Control
- Changes follow `docs/CHANGE_CONTROL.md`.
