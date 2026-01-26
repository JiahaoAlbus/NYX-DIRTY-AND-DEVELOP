# NYX iOS Reference Client (Testnet Beta)

Purpose
- Provide a SwiftUI reference client that mirrors deterministic flows and renders evidence verbatim.

Scope
- Connects to the NYX backend gateway API to run deterministic flows and fetch evidence bundles.
- Displays evidence fields verbatim and exports bundles without modification.

Non-Scope
- No user access flows, no identity model, no credential handoff, no real-money claims.
- No live market data, no trading claims, no protocol semantics.

Run (local)
- Start the backend gateway on http://127.0.0.1:8091.
- Open NYXPortal.xcodeproj in Xcode.
- Select an iPhone Simulator and Run.
 - Optional: set a custom backend URL in UserDefaults with key `nyx_backend_url`.

Rules
- Seed and run_id are required inputs.
- Evidence is read-only and is not computed or modified in the client.
- All outputs are deterministic for the same inputs.
