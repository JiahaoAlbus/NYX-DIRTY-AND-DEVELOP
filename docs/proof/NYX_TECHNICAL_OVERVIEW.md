# NYX Technical Overview

## Purpose
This document provides a factual, high-level technical overview of the NYX testnet portal infrastructure.

## System Architecture

NYX is a **testnet-only portal infrastructure** designed to demonstrate deterministic evidence generation and verifiable state transitions. It is NOT a blockchain, but a deterministic gateway system that produces cryptographically linked evidence trails.

### Core Components

1.  **NYX Backend Gateway**: A Python-based deterministic state machine.
    -   **Determinism**: Given a `seed` and `run_id`, the backend produces identical state transitions and outputs.
    -   **Evidence Bundle**: Every operation produces a JSON Evidence Bundle containing inputs, outputs, state hash, and receipt hashes.
    -   **Modules**:
        -   `wallet`: Simple UTXO-like balance tracking (testnet funds only).
        -   `exchange`: Order book and matching engine (deterministically seeded).
        -   `chat`: Signed message passing with room isolation.
        -   `entertainment`: Deterministic state generation (e.g., RNG sequences).

2.  **Conformance Runner**: A test suite that validates the backend against a formal ruleset (v1).
    -   Ensures no regression in invariants (e.g., fee > 0, additive platform fees).
    -   Verifies "No Fake Data" gates.

3.  **NYX World (Web)**: A React/Vite-based web interface.
    -   Visualizes the backend state.
    -   No business logic; purely a view layer over the deterministic backend.

4.  **NYX Portal (iOS)**: A native iOS shell wrapping a WebBundle.
    -   Demonstrates mobile delivery of the portal experience.
    -   Includes native Swift-side integration for "No Fake Data" verification.

## Key Invariants

1.  **Determinism**: `f(state, input, seed) -> (new_state, evidence)` is pure.
2.  **Identity != Portal Principals**: Authentication is decoupled from portal access control.
3.  **Protocol Fee > 0**: All state-mutating operations must burn or transfer a fee.
4.  **Additive Platform Fee**: Platforms (portals) can add fees on top, but cannot subtract protocol fees.
5.  **No Fake Data**: The system must fail visibly if the backend is offline or if data is tampered with. It does not mock data to "look working."

## Data Flow

1.  **Input**: Client sends signed request + seed + run_id.
2.  **Processing**: Gateway validates signature, checks balance, executes logic.
3.  **Evidence**: Gateway computes State Hash `H(state)` and Receipt Hash `H(receipt)`.
4.  **Output**: Returns `EvidenceBundle` { inputs, outputs, protocol_anchor, state_hash, receipt_hashes }.
5.  **Verification**: Client (or auditor) can replay the input sequence to verify the output hash matches.

## Infrastructure

-   **Testnet Only**: No connection to mainnet chains.
-   **Local/CI Execution**: Runs entirely in local environments or CI containers.
-   **No Database Dependency**: State is transient or file-based for the duration of the run (for reproducibility).
