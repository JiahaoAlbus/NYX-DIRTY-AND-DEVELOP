# L1 Chain Adapter + Devnet 0.1

This package implements a chain adapter interface and a deterministic in-memory devnet.

## Chain Adapter

- The adapter API is chain-scoped and does not model identity concepts.
- `ChainAccount` represents a chain-level sender only.
- Chain signatures are for inclusion/authorization only and do not define NYX identity.

## Hashing & Auditability

- `TxEnvelope`, `BlockRef`, and state roots use stable canonical encodings.
- `tx_hash`, `block_hash`, and `state_root` are reproducible offline.
- All bytes32 comparisons use constant-time `compare_digest`.

## Devnet 0.1

Deterministic in-memory chain with explicit mining and a minimal payload format:
- `0x01` SET(key,value)
- `0x02` DEL(key)
- `0x10` NOP

State root is computed from a stable serialization of sorted key/value pairs.

### Run

From `packages/l1-chain/src`:
```
python -m l1_chain.devnet.run_devnet
```

The run prints deterministic outputs for tx hashes, block refs, and state roots.

## No Privileged Paths

No allowlist, bypass, or debug free-lane mechanisms exist in this adapter.
