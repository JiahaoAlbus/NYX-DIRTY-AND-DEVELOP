# Protocol Snapshot (Current)

Purpose
- Provide an audit-grade snapshot of the currently executable protocol and its governing documents.

Scope
- Current `origin/main` state, including normative documents, machine semantics, and evidence commands.

Non-Scope
- Any new protocol semantics, refactors, or non-deterministic behavior.

Version Anchor
- HEAD: `9e795f461931301344445286e463ce2450fc9a6c`
- Describe: `testnet-0.2-68-g9e795f4`
- Tags: `testnet-0.1`, `testnet-0.2`

Normative Documents (Legal Protocol Definition)
- `docs/DEX_V1_BLUEPRINT.md` — DEX v1 blueprint and v0 strict subset rules; defines state/actions/receipts boundaries.
- `docs/DEX_V1_ROUTER_BLUEPRINT.md` — Router v1 blueprint, atomicity, receipt rules, and fee integration boundaries.
- `docs/INVARIANT_MAP_DEX.md` — DEX v0 invariant map with evidence references.
- `docs/INVARIANT_MAP_DEX_V1.md` — Router v1 invariant map with evidence references.
- `docs/DEX_SECURITY_CASE.md` — Security claims and evidence mapping for DEX and router.
- `docs/CHANGE_CONTROL.md` — Change control and patch-only policy for sealed semantics.
- `docs/REFERENCE_CLIENT_SPEC.md` — Reference client contract and determinism requirements.
- `docs/RELEASE_PROCESS_Q5.md` — Q5 release process and gating rules.
- `docs/MAINNET_LAUNCH_CHECKLIST.md` — Objective Go/No-Go criteria (additive Q5 items only).
- `docs/AUDIT_PACK_Q5.md` — Audit pack summary and evidence mapping.
- `docs/AUDIT_REPRO_COMMANDS.md` — Canonical verification commands.
- `docs/SECURITY_DISCLOSURE_PROCESS.md` — Disclosure requirements and evidence format.
- `docs/NYX_Q3_IMMUTABLE_RULES.md` — Immutable rules index from Q3 baseline.

Machine Semantics (Code Truth)

DEX v0
- Actions: `packages/l3-dex/src/l3_dex/actions.py`
  - `ActionKind`, `CreatePool`, `AddLiquidity`, `RemoveLiquidity`, `Swap`
- State: `packages/l3-dex/src/l3_dex/state.py`
  - `PoolState`, `DexState`
- State Transition: `packages/l3-dex/src/l3_dex/kernel.py`
  - `apply_action(state, action)`
- Receipts: `packages/l3-dex/src/l3_dex/receipts.py`
  - `DexReceipt`
- Replay: `packages/l3-dex/src/l3_dex/replay.py`
  - `replay_receipt(state, receipt)`
- Invariants: `packages/l3-dex/src/l3_dex/invariants.py`
  - `check_invariants(state)`

Router v1
- Actions: `packages/l3-router/src/l3_router/actions.py`
  - `RouterActionKind`, `RouteSwap`, `RouterAction`
- State: `packages/l3-router/src/l3_router/state.py`
  - `RouterState`, `state_hash(state)`
- State Transition: `packages/l3-router/src/l3_router/kernel.py`
  - `apply_route(state, action)`
- Receipts: `packages/l3-router/src/l3_router/receipts.py`
  - `RouterReceipt` (includes step receipts)
- Replay: `packages/l3-router/src/l3_router/replay.py`
  - `replay_route(state, receipt)`
- Invariants: `packages/l3-router/src/l3_router/invariants.py`
  - `check_invariants(state)`
- Fee binding: `packages/l3-router/src/l3_router/fee_binding.py`
  - `quote_fee_for_route`, `enforce_fee_for_route`

Fee Enforcement
- Engine: `packages/l2-economics/src/engine.py`
  - `FeeEngineV0.quote`, `FeeEngineV0.enforce`

Receipt / Replay Contract
- DEX receipt schema: `packages/l3-dex/src/l3_dex/receipts.py`
- Router receipt schema: `packages/l3-router/src/l3_router/receipts.py`
- Replay rules: `packages/l3-dex/src/l3_dex/replay.py`, `packages/l3-router/src/l3_router/replay.py`
- Deterministic hash use: compare_digest in replay and fee enforcement pathways.

Invariant Enforcement Evidence

Invariant Category -> Evidence
- DEX invariants (non-negative reserves, deterministic replay)
  - `packages/l3-dex/test/bounded_explorer_test.py`
  - `packages/l3-dex/test/golden_vectors_test.py`
- Router invariants (atomicity, replay correctness)
  - `packages/l3-router/test/unit_atomic_failure_test.py`
  - `packages/l3-router/test/unit_replay_test.py`
  - `packages/l3-router/test/golden_vectors_test.py`
- Fee invariants (mutation fee > 0, sponsor equivalence)
  - `packages/l3-router/test/unit_fee_nonzero_test.py`
  - `packages/l3-router/test/unit_sponsor_equivalence_test.py`
  - `packages/l2-economics/test/property_fee_invariants_test.py`
- Property invariants (PROPERTY_N)
  - `packages/l3-router/test/property_router_invariants_test.py`
- Conformance drills
  - `packages/conformance-v1/src/conformance_v1/drills.py`

Deterministic Demos / Reference Clients
- Private transfer demo: `packages/e2e-private-transfer/src/e2e_private_transfer/run_demo.py`
  - Outputs: fee_total, tx_hash prefix, block_hash prefix, state_root prefix, receipt_hash prefix, replay_ok.
- E2E demo: `packages/e2e-demo/src/e2e_demo/run_demo.py`
  - Outputs: commitment prefix, fee total, tx hash prefix, block hash prefix, state root prefix, receipt hash prefix, replay_ok.
- Reference client CLI: `attic/apps/nyx-reference-client/src/nyx_reference_client/cli.py`
  - Outputs: state_hash, receipt_chain, replay_ok.

Canonical Verification Commands
- Compile: `python -m compileall packages/l0-identity/src`
- Tests: `python -m unittest discover -s packages/l0-identity/test -p "*_test.py" -v`
- Conformance runner: `PYTHONPATH="packages/conformance-v1/src" python -m conformance_v1.runner --out /tmp/nyx_conformance_report.json`

Freeze / Change Control
- This snapshot is a read-only report and does not change protocol semantics.
- Change control rules apply as defined in `docs/CHANGE_CONTROL.md`.
