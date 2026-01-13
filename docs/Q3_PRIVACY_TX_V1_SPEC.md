# Q3 Privacy Tx v1 Spec

## 1) Scope
This week: freeze the privacy transaction track, write the spec, and land skeleton packages.
Not in scope: UI, performance claims, production cryptography, rollup proofs, or confidential transfer UX.

## 2) Chosen Track
Track B: privacy pool / private transfer (commitment + nullifier + replaceable ZK).
Why not A (mixing) or C (protocol bridge):
- B matches the existing commitment/nullifier model and context separation.
- B integrates cleanly with fee and chain without new semantics.
- B is the smallest spec that still preserves auditability.

## 3) Data Model
All hashes are bytes32. Strings are UTF-8. Integers are non-negative.

- Note:
  - note_id: bytes32
  - commitment: bytes32
  - value: int
  - memo: str | None
- Commitment:
  - value: bytes32
- Nullifier:
  - value: bytes32
- LedgerRoot:
  - value: bytes32

## 4) Invariants
Inherited:
- Mutation requires a non-zero fee.
- Proof context separation must hold.
- Sender and signature carry no identity meaning.

Q3 v1:
- Nullifier reuse is forbidden.
- No cross-context link is permitted.
- Ledger root is deterministic from note state.

## 5) Proof Binding
Envelope binds:
- context_id
- statement_id
- nonce
- ledger_root
- action_hash
- public_inputs

Binding enforces context separation; reuse under a different context must fail.

## 6) Fee & Chain Integration
Private actions still flow through fee engine and chain adapter.
Fee calculation must not depend on sender or signature.

## 7) Replaceable ZK Plan
Mock proof now; real prover/verifier later via stable interfaces.
Interfaces will expose Prover and Verifier only, not protocol logic.

## 8) Security Notes
- Prevent cross-context link.
- Prevent replay via nullifier reuse.
- Prevent trace tampering via replay checks.

## 9) Acceptance for Week1
- Spec is frozen in this file.
- Skeleton packages are present with types and interfaces.
- Q3 test bridge loads new tests under CI discovery.
