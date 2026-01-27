# iOS Runbook (Testnet Beta)

## Purpose
Provide exact steps to run the NYX iOS app against the local backend.

## Preconditions
- Backend gateway running on `http://127.0.0.1:8091`.
- Xcode installed with an iOS Simulator.

## Start Backend
Run:
- `scripts/nyx_backend_dev.sh`

Verify:
- `curl http://127.0.0.1:8091/healthz` returns `{ "ok": true }`.

## Run iOS App
1) Build the WebBundle (only when nyx-world changes):
   - `scripts/build_nyx_world.sh`
2) Open `apps/nyx-ios/NYXPortal.xcodeproj` in Xcode.
3) Select an iPhone Simulator.
4) Run.

## Backend URL Override
- Default base URL: `http://127.0.0.1:8091`.
- Override in Settings using the `nyx_backend_url` UserDefaults key (UI provides a field).

## Offline Behavior
- If backend is unreachable, the app must show a “Backend Offline” banner and never crash.
- Evidence Center remains available for previously fetched runs and export downloads when backend is back online.

## Testnet Only
- All UI copy must remain Testnet Beta and must not claim mainnet connectivity.
