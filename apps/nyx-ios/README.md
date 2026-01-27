# NYX iOS Client (Testnet Beta)

Purpose
- Provide a SwiftUI client that calls the backend gateway and renders evidence verbatim.

Scope
- Portal account and chat flows (testnet only).
- Wallet faucet and transfer (testnet only).
- Exchange, marketplace, entertainment flows backed by the gateway.
- Evidence export via backend endpoints.

Non-Scope
- No mainnet claims or external wallet linking.
- No KYC or personal identity binding.

Run (local)
1) Start backend:
   - `scripts/nyx_backend_dev.sh`
2) Build the WebBundle (only when updating nyx-world UI):
   - `scripts/build_nyx_world.sh`
3) Open `apps/nyx-ios/NYXPortal.xcodeproj` in Xcode.
4) Select an iPhone Simulator and Run.
5) Optional backend override:
   - In Settings, set the backend URL (stored under `nyx_backend_url`).

Xcode build (CLI)
- `xcodebuild -project apps/nyx-ios/NYXPortal.xcodeproj -scheme NYXPortal -destination 'platform=iOS Simulator,name=iPhone 16 Pro' build`

Rules
- Seed and run_id are required for evidence flows.
- Evidence fields are rendered and exported verbatim from the backend.
- All outputs are deterministic for the same inputs.
