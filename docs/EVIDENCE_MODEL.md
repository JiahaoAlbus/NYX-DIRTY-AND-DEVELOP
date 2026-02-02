# NYX Evidence Model

This document defines the structure and verification logic of NYX Evidence.

## 1. The Evidence Bundle
An `EvidenceBundle` is a self-contained package that proves the validity of a sequence of operations.

### Structure
- **Seed**: The deterministic entropy source.
- **Run ID**: A unique identifier for the execution session.
- **Inputs**: A chronological list of all user inputs and environmental factors.
- **Outputs**: The resulting state transitions and artifacts.
- **State Hash**: A Merkle-tree rooted hash of the final protocol state.
- **Receipt Hashes**: A list of hashes for every individual operation in the run.
- **Replay Status**: A boolean flag indicating if the local replay matched the server-provided hash.

## 2. Verification Logic
Any third party can verify a run by following these steps:
1. **Initialize**: Set up a clean protocol environment with the provided `seed`.
2. **Replay**: Apply each item in the `Inputs` list sequentially to the state machine.
3. **Compare**: After all inputs are processed, compute the local `state_hash`.
4. **Assert**: If `local_state_hash == evidence.state_hash`, the run is verified.

## 3. Protocol Enforcement
- **Transparency**: All evidence bundles are public and exportable as `.zip` files.
- **Immutability**: Once an evidence bundle is finalized and anchored, its inputs cannot be changed without invalidating the `state_hash`.
- **Completeness**: Evidence MUST include all external calls (e.g., Web2 API responses) to ensure a perfectly reproducible environment.

## 4. The "No-Fake" Rule
Evidence MUST NOT contain synthetic or "mocked" data in place of actual protocol logic. Every entry in the `Outputs` list must be a direct result of the deterministic execution of the `Inputs`.
