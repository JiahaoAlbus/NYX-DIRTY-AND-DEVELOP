# L2 Private Ledger (Skeleton)

This package defines the private ledger v0 state machine for Q3 v1.

## Scope
- Types: Note, Commitment, Nullifier, LedgerRoot
- Deterministic state root from commitment/nullifier sets
- Trace and replay verification for tamper detection
- Interfaces: private ledger kernel and stores
- Proof wiring to l0-zk-id envelope for private ledger actions

## Non-goals
- No chain integration
- No sender semantics
- No persistence layer
