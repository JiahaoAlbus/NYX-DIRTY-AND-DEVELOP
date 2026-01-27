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
1) Open `apps/nyx-ios/NYXPortal.xcodeproj` in Xcode.
2) Select an iPhone Simulator.
3) Run.

## Backend URL Override
- Default base URL: `http://127.0.0.1:8091`.
- Override in Settings using the `nyx_backend_url` UserDefaults key (UI provides a field).

## Offline Behavior
- If backend is unreachable, the app must show a “Backend Offline” banner and never crash.

## Testnet Only
- All UI copy must remain Testnet Beta and must not claim mainnet connectivity.
