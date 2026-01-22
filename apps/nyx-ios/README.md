# NYX iOS Reference Client (Testnet Alpha)

Purpose
- Provide a SwiftUI reference client that mirrors deterministic flows and renders evidence verbatim.

Scope
- Connects to the NYX backend gateway API to run deterministic flows and fetch evidence bundles.
- Displays evidence fields verbatim and exports bundles without modification.

Non-Scope
- No user access flows, no identity model, no credential handoff, no funds display, no chat history.
- No live market data, no trading claims, no protocol semantics.

Run (local)
- Open the folder in Xcode.
- Ensure the backend gateway is running on localhost:8091.
- Build and run on a simulator.

Rules
- Seed and run_id are required inputs.
- Evidence is read-only and is not computed or modified in the client.
- All outputs are deterministic for the same inputs.
