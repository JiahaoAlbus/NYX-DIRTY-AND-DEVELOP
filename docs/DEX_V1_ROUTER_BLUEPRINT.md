# DEX v1 Router Blueprint (F0)

Purpose
- Define Router v1 interfaces, receipt schema, and atomicity rules.

Scope
- Router actions, receipts, replay contract, rounding rules, and bounds.

Non-Scope
- New swap math beyond the existing v0 swap.
- Any account binding semantics.
- Production bridge or on/off ramp logic.

MUST and MUST NOT
- Router MUST compose only v0 swap actions defined in `l3_dex.actions.Swap`.
- Router MUST be atomic: any step failure MUST leave state unchanged.
- Router MUST use integer arithmetic only; floats are forbidden.
- Router MUST apply explicit bounds:
  - steps count MUST be within [1, 8].
  - amount_in MUST be > 0.
  - min_out MUST be >= 0.
- Router MUST produce deterministic receipts with stable ordering.
- Router MUST NOT introduce account or signer semantics.
- Router MUST use existing fee enforcement; no parallel fee pathway.
- Router MUST NOT leak secrets or witness material.

Interface (F0)
- RouteSwap
  - steps: tuple of v0 Swap actions
- RouterAction
  - kind: ROUTE_SWAP
  - payload: RouteSwap

Receipt schema (F0)
- RouterReceipt
  - action: RouterActionKind
  - state_hash: bytes
  - step_receipts: tuple of DexReceipt

Replay contract
- replay_route(state, receipt) MUST reproduce the receipt state_hash.
- Determinism is required across machines.

Rounding rules
- All arithmetic is integer-only.
- Router uses v0 swap rounding behavior for each hop.

Evidence / Verification
- Week02: skeleton import tests.
- Week03: bounded explorer notes.
- Week04: golden vector tests.
- Week05: property tests at PROPERTY_N.
- Week08: conformance drills.

Freeze / Change Control
- F0: Router interface and receipt schema are locked after Week02.
- After F0: patch-only or additive extensions; semantic changes require a new version.
