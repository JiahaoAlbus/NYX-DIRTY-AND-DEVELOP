# NYX Architecture Map

This document maps the top-level components, entrypoints, and data flows.

## 1) Top-Level Layout

```
apps/                       # Runtime services
  nyx-backend-gateway/      # Gateway API + Web2 guard + state mutations
  nyx-backend/              # Evidence runner + artifacts
  nyx-ios/                  # iOS app (SwiftUI + WebBundle)
packages/                   # Libraries & extension
  extension/                # MV3 browser extension (EIP-1193)
nyx-world/                  # Web portal (Vite/React)
scripts/                    # Verification, build, ops
conformance/                # Frozen rules gate + checks
deploy/                     # Free-tier deployment templates
docs/                       # Product/security/ops docs
```

## 2) Entrypoints

**Gateway API**
- Command: `python -m nyx_backend_gateway.server`
- Port: `8091` (default)
- Responsibility: capabilities, wallet/exchange/store/chat endpoints, Web2 guard, evidence adapter.

**Evidence Runner**
- Command: `python -m nyx_backend.server`
- Port: `8090` (default)
- Responsibility: deterministic evidence generation & export.

**Web Portal**
- Command: `npm run dev` in `nyx-world`
- Responsibility: UX/UI, capability-driven rendering, calls gateway.

**iOS App**
- Xcode project: `apps/nyx-ios/NYXPortal.xcodeproj`
- SwiftUI shell + embedded WebBundle (built from `nyx-world`).

**Browser Extension**
- Source: `packages/extension`
- Built in release pipeline; exposes EIP‑1193 provider.

## 3) Data Stores

- **Gateway DB**: `apps/nyx-backend-gateway/data/nyx_gateway.db` (SQLite)
- **Evidence Runs**: `apps/nyx-backend-gateway/runs/` + `docs/evidence/`

## 4) High-Level Data Flow

```
User -> Web Portal / iOS / Extension
     -> Gateway API (auth + capabilities + state mutation)
        -> Web2 Guard (allowlist, bounds, logging)
        -> Evidence Runner (deterministic receipts/state_hash)
        -> Storage (SQLite)
     -> Evidence Replay (verify)
```

## 5) Internal Dependencies (One-Way)

- `nyx-world` (UI) depends on Gateway API only.
- `nyx-backend-gateway` depends on `nyx-backend` for evidence.
- `packages/*` are leaf dependencies; no cycles back into apps.

## 6) Capability-Driven UI

- The UI renders modules based on `/capabilities`.
- Missing capability => feature hidden/disabled (no fake buttons).

## 7) CI/Conformance

- Workflow: `.github/workflows/ci.yml`
- Frozen rules: `conformance/run.sh`
- Verification script: `scripts/nyx_verify_all.sh`
