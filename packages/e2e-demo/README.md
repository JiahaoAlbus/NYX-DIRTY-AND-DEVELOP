# Week 7 E2E Demo

This package wires identity proof, fee quote/receipt, chain submission, and trace replay into a single deterministic pipeline.

## Run demo
- Command: `python -m e2e_demo.run_demo --out /tmp/nyx_w7_trace.json --seed 123`
- Output: summary line with commitment prefix, fee total, tx hash, block hash, state root, receipt hash, replay_ok

## Invariants
- Fee for mutation is non-zero
- Proof verification is context-bound; wrong context fails
- Chain sender/signature is not identity
- Trace contains no root secret

## Trace fields
- Identity: commitment hex
- Proof: envelope fields (context/statement/public inputs/proof bytes/binding tag)
- Action: descriptor payload + action hash
- Fee: vector components + quote hash + receipt hash
- Chain: tx envelope fields, block ref, state root, state proof

## Replay
- Recompute proof binding verification
- Recompute fee quote and receipt hashes
- Rebuild tx envelope and replay devnet
- Verify state proof and finality proof against replayed chain
