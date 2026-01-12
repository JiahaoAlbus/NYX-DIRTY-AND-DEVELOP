# Audit Checklist — NYX Testnet 0.1

Phase 0 — Clean Room
[ ] git status must be clean  
    - `git status`
[ ] main must be up to date  
    - `git checkout main && git pull`
[ ] Record HEAD for audit  
    - `git rev-parse HEAD`

Phase 1 — CI-Equivalent Gate
[ ] compile passes  
    - `python -m compileall packages/l0-identity/src`
[ ] Full tests (CI discovery equivalent) pass  
    - `python -m unittest discover -s packages/l0-identity/test -p "*_test.py" -v`  
    PASS: output ends with `OK` and zero failures

Phase 2 — E2E Integrity
[ ] E2E demo reproducible (seed=123)  
    - `PYTHONPATH="packages/l0-identity/src:packages/l2-economics/src:packages/l1-chain/src:packages/wallet-kernel/src:packages/l0-zk-id/src:packages/e2e-demo/src" python -m e2e_demo.run_demo --out /tmp/nyx_w7_trace.json --seed 123`  
    PASS: output includes `replay_ok=True`
[ ] Replay verification  
    - Demo embeds replay; trace includes receipt/proof hashes for offline verification

Phase 3 — Conformance/Red-Team Training Ground
[ ] conformance-v1 tests covered in Phase 1 (bridge-discovered)  
    PASS: `guard_no_false_negative`, `guard_no_frozen_gate_sequence`, and runtime drill tests appear and pass
[ ] (Optional) conformance-v1 runner  
    - `PYTHONPATH="packages/conformance-v1/src" python -m conformance_v1.runner`  
    PASS: exit code 0

Phase 4 — Freeze & Tag
[ ] Tag only from main  
    - `git checkout main && git pull`
[ ] Create annotated tag  
    - `git tag -a testnet-0.1 -m "NYX Testnet 0.1"`
[ ] Push tag  
    - `git push origin testnet-0.1`
[ ] (Optional) GitHub Release  
    - `gh release create testnet-0.1 -t "NYX Testnet 0.1" -n "<release notes summary>"`

Fail Fast: if any item fails, stop the release.  
No Override: do not bypass the checklist via temporary switches or shortcuts.  
Break-Glass only: any fix touching sealed foundations requires formal break-glass.
