# NYX Technical Overview

## 1. What NYX Is
NYX is a testnet-only portal infrastructure that stitches together a deterministic backend gateway, evidence generation layer, and multiprotocol UI surfaces (web + iOS). It is primarily an enforcement/verification platform: every request that mutates shared state produces byte-identical evidence bundles (protocol_anchor, inputs, outputs, receipt_hashes, state_hash, replay_ok, stdout) that can be replayed off-line. The codebase enforces fee invariants (protocol fee > 0, additive platform fee) and forbids identity/account semantics, keeping “NYX identity” separate from portal-level principals. The repository includes real modules for wallet/faucet, exchange, chat, marketplace, entertainment, and evidence orchestration, all of which can be started locally via documented scripts and validated by deterministic smoke tests.

## 2. System Architecture and Portal-Level Scope
- **Gateway:** `apps/nyx-backend-gateway/src` exposes modular HTTP endpoints under `/wallet`, `/exchange`, `/chat`, `/marketplace`, `/entertainment`, `/portal`, and `/evidence`. Each handler enforces strict validation, rate limits, fee accounting, and produces canonical evidence via `nyx_backend`.
- **Evidence Stack:** `packages/wallet-kernel` and the associated `nyx_backend.evidence` module produce and verify `EvidenceBundle` objects, enforce compare-digest usage, and guard JNI context separation. Drift in ordering or missing fields is treated as fatal.
- **UI Layer:** Both the WKWebView-bundled React/Vite app (`nyx-world`) and the native iOS shell (`apps/nyx-ios`) are wired to these gateway endpoints, overriding the backend URL via settings and surfacing offline/offloading behavior without introducing placeholder data.
- **Verification and Flow Guards:** Scripts (`nyx_smoke_all_modules.py`, `scripts/nyx_fundraising_validate.sh`) orchestrate end-to-end flows covering all modules, plus no-fake-code gates that scan runtime sources for banned keywords in Web/Swift code.
Collectively, this integration makes NYX a portal-level ecosystem: one entry point (web/ios) controls multiple distinct services, all anchored by a shared evidence ledger and compliance rules rather than a single-purpose dApp.

## 3. Verifiable Technical Facts
- **Deterministic Tests:** `scripts/nyx_run_all_unittests.py` runs 585+ tests, covering storage, fee invariants, evidence ordering, red-team guards, private-ledger properties, and UI asset presence; logs print `PROPERTY_N=2000`.
- **Smoke Harness:** `scripts/nyx_smoke_all_modules.py` executes wallet faucet/transfer, exchange orders, chat rooms/messages, marketplace listings/purchases, entertainment steps, and evidence downloads; artifacts are stored under `docs/evidence/...`.
- **Evidence Generation:** Backend modules import `nyx_backend.evidence` to create receipts, and CI guards (e.g., `guard_no_fake_tokens_test`) ensure Web/iOS sources cannot emit mock data. Evidence bundles are recorded verbatim via `_record_evidence` and zipped deterministically (`export.zip` comparisons).
- **Operations Scripts:** `scripts/build_nyx_world.sh`, `scripts/nyx_backend_dev.sh`, and `scripts/nyx_fundraising_validate.sh` publish reproducible CLI flows (backend start, smoke run, compile/test/conformance/xcode build).
- **Conformance:** `packages/conformance-v1` contains drills for UI copy, evidence ordering, fee independence, anti-traversal, and guard tests (`guard_no_frozen_gate_sequence`). The runner outputs `nyx_conformance_report.json`.
- **UI Resources:** The WebBundle (`apps/nyx-ios/WebBundle/`) includes the built `nyx-world` React app; runtime Web/Swift files avoid forbidden strings (enforced by `scripts/no_fake_gate_*` and iOS guard test).

## 4. Risks and Limitations
- **Mainnet Not Implemented:** All discoveries explicitly state “Testnet Beta”; there is no mainnet deployment, no multi-sig settlement, and no bridge to external chains.
- **Tokens Still Testnet:** “NYXT” and similar symbols exist only as deterministic internal units, with faucet caps and treasury routing documented. No market prices or external integrations.
- **Scaling & Ops:** The current stack runs locally via SQLite/Python; there is no distributed coordinator, high-availability layer, or monitoring stack beyond simple scripts. Horizontal scaling must be designed later.
- **UI Polish:** The React/Vite UI and iOS shell prioritize functionality and evidence export; aesthetics are present but intentionally trade realism for deterministic behavior (“no fake data” banners remain when backend offline).
- **Limited Authentication:** Portal accounts use local Ed25519 keypairs and signed challenges; they are pseudonymous and purpose-built for the portal. There is no registration via email/phone or KYC workflow.

## 5. Why This Can Be Extended into a Full Web3 Network
- **Modular Evidence Backbone:** Every module already emits canonical evidence and obeys fee contracts. The backend can be extended with additional protocols (staking, governance, bridging) without changing the established evidence schema.
- **Multi-Entry Interfaces:** Web and iOS shells already host multiple services (wallet, exchange, chat, marketplace, entertainment). Adding new APIs or services simply involves binding them to the existing navigation/routing infrastructure.
- **Ops Tooling:** Scripts exist to start services, run deterministic smoke tests, and validate CI; this automation is essential for onboarding partners or auditors.
- **Guarded Policy & Conformance:** The repository includes extensive guard tests, security docs, and no-fake gates, creating a compliance-ready baseline for future partners.
- **Fee/Treasury Framework:** Protocol and platform fees already route to configurable addresses, ensuring economic interactions can be audited and extended to real treasury workflows when on-chain bridges are added.


