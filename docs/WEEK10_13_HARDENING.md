# Week10–13 Buffer & Hardening

## Scope
- Bugfix only: deterministic behavior, stronger validation, stable outputs
- Test expansion: more negative cases and replay tamper checks
- Q3 interface stubs only (no runtime implementation)

## Invariants (unchanged)
- Identity is separate from account and sender
- State mutation must carry a non-zero fee
- Proof context separation must hold
- Client kernel remains verify-only
- Sender/signature carry no identity meaning

## How to run
```bash
python -m compileall packages/l0-identity/src
python -m unittest discover -s packages/l0-identity/test -p "*_test.py" -v
```

```bash
PYTHONPATH="packages/l0-identity/src:\
packages/l2-economics/src:\
packages/l1-chain/src:\
packages/wallet-kernel/src:\
packages/l0-zk-id/src:\
packages/e2e-demo/src" \
python -m e2e_demo.run_demo --out /tmp/nyx_w7_trace.json --seed 123
```

```bash
PYTHONPATH="packages/conformance-v1/src" \
python -m conformance_v1.runner --out /tmp/nyx_conformance_report.json
```

## Not allowed
- Any free mutation path
- Skipping verify or replay checks
- Special-cased shortcut routes
