# NYX Decentralization Model

This document outlines the current state and future path of decentralization for the NYX Protocol.

## 1. Current State (Testnet Beta)
The NYX Testnet is currently in a **Phase 1: Deterministic Federation** stage.

### Centralized Components (By Design)
- **Gateway**: Acts as the primary sequencer for ordering transactions.
- **Treasury Address**: Managed by the NYX Foundation for ecosystem development.
- **Identity Service**: Handles account creation and session challenges.

### Decentralized Features (Active)
- **Verifiable Evidence**: Every transaction produces a hash-linked receipt that can be independently verified.
- **Client-Side Sovereignty**: All cryptographic keys are generated and stored on-device (iOS/Web).
- **Deterministic Replay**: Any node can reconstruct the global state from the evidence bundle.

## 2. The Path to Decentralization

### Phase 2: Multi-Sequencer Federation
- Introduce multiple gateway nodes with a BFT (Byzantine Fault Tolerance) consensus.
- Transition from a single treasury to a multisig governance model.

### Phase 3: Permissionless Verification
- Open the evidence verification layer to the public.
- Implement ZK-proofs (Zero-Knowledge) for state transitions to reduce verification overhead.

### Phase 4: Full Decentralization
- Transition to a DAO-controlled governance for protocol upgrades.
- Decentralize the identity service using decentralized identifiers (DIDs).

## 3. Guarantees
Even in its current centralized gateway stage, NYX guarantees:
1. **Auditability**: The gateway cannot lie about the outcome of a transaction without being caught by evidence replay.
2. **Privacy**: The gateway cannot read user messages or private keys.
3. **Reproducibility**: The protocol behavior is strictly governed by the open-source code, not by arbitrary server logic.
