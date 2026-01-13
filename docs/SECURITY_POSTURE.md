# Security Posture (Phase-2)

## Commitments
- Enforce non-zero fees on state mutation
- Enforce proof context separation
- Verify-only client kernel for proof handling
- Conformance drills fail fast on rule violations

## Non-commitments
- Not a production cryptography promise
- Not a hardware or enclave key management promise

## How we prevent shortcut paths
- Fee engine rejects zero-fee mutation
- Proof envelope binding is recomputed on verify
- Conformance gates scan for forbidden patterns

## How we self-audit
```bash
python -m compileall packages/l0-identity/src
python -m unittest discover -s packages/l0-identity/test -p "*_test.py" -v
PYTHONPATH="packages/conformance-v1/src" python -m conformance_v1.runner --out /tmp/nyx_conformance_report.json
```
