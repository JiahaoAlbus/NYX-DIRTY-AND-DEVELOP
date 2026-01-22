# NYX iOS Reference Client (Q8 Week08)

Purpose
- Provide a SwiftUI reference client that mirrors the web flows and renders evidence deterministically.

Scope
- Connects to the NYX backend API to run deterministic flows and fetch evidence bundles.
- Displays evidence fields verbatim and exports bundles without modification.

Non-Scope
- No login, no account model, no wallet connect, no balances, no chat history.
- No live market data, no trading, no protocol semantics.

Run (local)
- Open the folder in Xcode.
- Set the backend base URL in `GatewayClient` if needed.
- Build and run on a simulator.

Rules
- Seed and run_id are required inputs.
- Evidence is read-only and is not computed or modified in the client.
- All outputs are deterministic for the same inputs.
