# Dead Code & Dependency Report

Date: 2026-02-08

This report documents **verified dead code removal** and **candidate cleanups**. Where possible, the code was removed in this pass; if removal was unsafe without deeper product validation, it is explicitly listed as a deferred candidate.

## Removed in this pass (evidence-based)

### Gateway legacy validation + Web2 allowlist helpers
- **Removed:** legacy `_require_*`, `_validate_*`, `_WEB2_*` helpers and duplicated allowlist/constants from `apps/nyx-backend-gateway/src/nyx_backend_gateway/gateway.py`.
- **Reason:** These paths were no longer referenced after refactor to dedicated modules.
- **Evidence:** All validation now flows through `nyx_backend_gateway.validation` and Web2 guard through `nyx_backend_gateway.web2_guard` (see `execute_run`, `execute_wallet_*`, and `execute_web2_guard_request` wrappers). No internal references remained.
- **Impact:** Single source of truth for validation & Web2 guard; reduced drift risk.

### Gateway unused imports and dataclasses
- **Removed:** Unused `storage` imports (e.g., `EvidenceRun`, `Receipt`, `Listing`, `Purchase`, `MessageEvent`, `Web2GuardRequest`) and unused helper `apply_wallet_faucet`.
- **Reason:** The refactor routes evidence via `evidence_adapter.run_and_record` and marketplace/chat/web2 via dedicated modules.

### Web2 guard test patch target
- **Updated:** `apps/nyx-backend-gateway/test/server_web2_guard_test.py` now patches `web2_guard._web2_request` instead of the removed gateway helper.
- **Reason:** Gateway no longer hosts Web2 HTTP logic.

### Frontend dependency cleanup (nyx-world)
- **Removed:** `lightweight-charts` from `nyx-world/package.json` and `nyx-world/package-lock.json`.
- **Reason:** No references in portal code; dependency was unused.
- **Evidence:** `grep -R "lightweight-charts" -n nyx-world --exclude-dir=node_modules --exclude-dir=dist` returned only package manifest hits.

## Deferred candidates (needs deeper product verification)

### Duplicate repository snapshot
- **Candidate:** `NYX-DIRTY-AND-DEVELOP/` appears to contain a duplicate tree.
- **Reason to defer:** Could be a vendor snapshot or release mirror; removal requires product owner confirmation.

### Frontend dependency trimming
- **Candidate:** Additional `nyx-world/package.json` dependencies.
- **Reason to defer:** Usage confirmed for `material-symbols`, `lucide-react`, and `@noble/hashes`; further trimming requires bundle analysis to avoid regressions.

## Next audit steps (recommended)
1. Run bundle analysis on `nyx-world` to confirm unused deps.
2. Review iOS build scripts for unreferenced assets or duplicate resources.
3. Cross-check `scripts/` and `tooling/` for unused or legacy-only scripts.
