# NYX Testnet 0.1 Runbook

Goal: a new user can validate the sealed stack and run the Week7 end-to-end demo in ~10 minutes.

## Environment
- Python 3.11+ recommended
- Stdlib only (no external deps)
- Git with access to the `testnet-0.1` tag

## One-Command Sequence (copy/paste)
```bash
# 1) Checkout the frozen tag
git checkout testnet-0.1

# 2) CI-equivalent tests (same as pipeline)
python -m compileall packages/l0-identity/src
python -m unittest discover -s packages/l0-identity/test -p "*_test.py" -v

# 3) Week7 E2E demo (deterministic seed)
PYTHONPATH="packages/l0-identity/src:packages/l2-economics/src:packages/l1-chain/src:packages/wallet-kernel/src:packages/l0-zk-id/src:packages/e2e-demo/src" \
python -m e2e_demo.run_demo --out /tmp/nyx_w7_trace.json --seed 123
```

## Expected Output (prefixes ok)
- `unittest` ends with `OK`
- Demo prints: `identity_commitment=<hex prefix> fee_total>0 tx_hash=<hex prefix> block_hash=<hex prefix> state_root=<hex prefix> receipt_hash=<hex prefix> replay_ok=True`
- Trace file written to `/tmp/nyx_w7_trace.json`

## Troubleshooting (fail fast)
1) Python path errors: ensure the full `PYTHONPATH` from the command is copied exactly.
2) Dirty git tree: `git status` must be clean before running.
3) Missing tag: run `git fetch --tags` then retry checkout.
4) Permission denied on /tmp: pick another writable path for `--out`.
5) Demo replay failure: delete the old trace and rerun the demo with the exact seed `123`.
