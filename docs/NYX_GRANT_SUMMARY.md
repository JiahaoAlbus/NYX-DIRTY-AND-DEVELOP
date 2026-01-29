# NYX — Technical Grant Summary

## 1. What NYX Is
NYX is a testnet-only portal infrastructure that integrates a deterministic backend gateway, a canonical evidence generation layer, and multi-surface user interfaces (Web and iOS). It is not a single-purpose dApp, but a portal-level enforcement and verification system.

Every state-mutating request executed through NYX produces a byte-identical EvidenceBundle containing protocol anchors, inputs, outputs, receipt hashes, state hashes, replay verification flags, and stdout traces. These bundles can be replayed and verified offline without relying on NYX runtime services.

NYX explicitly separates portal-level principals from identity or account semantics. There are no user identities, balances, or accounts in the traditional sense. All interactions are protocol-scoped, fee-enforced, and evidence-backed.

---

## 2. System Architecture
- **Gateway Layer**: Modular HTTP endpoints under `/wallet`, `/exchange`, `/chat`, `/marketplace`, `/entertainment`, `/portal`, and `/evidence`, enforcing validation, fee invariants, and deterministic execution.
- **Evidence Layer**: Canonical EvidenceBundle generation and verification with strict ordering, digest comparison, and replay guarantees. Drift or missing fields are treated as fatal errors.
- **UI Surfaces**: A React/Vite web application bundled into an iOS WKWebView shell, plus native iOS surfaces for evidence inspection and settings. No mock or placeholder data is allowed.
- **Guards & Policy**: Repository-wide “no-fake-code” gates prevent simulated data, mock tokens, or placeholder logic in Web and iOS sources.

---

## 3. Verifiable Technical Facts
- Deterministic unit tests covering storage, fees, evidence ordering, and security guards.
- End-to-end smoke harness executing wallet, exchange, chat, marketplace, entertainment, and evidence export flows.
- Conformance runner validating UI copy, protocol invariants, and evidence schemas.
- Reproducible build scripts for backend, WebBundle, and iOS shell.

All verification steps are executable locally via documented CLI commands.

---

## 4. Limitations
- Testnet-only system; no mainnet deployment.
- No external token listings, bridges, or settlement.
- No KYC, email, or phone-based authentication.
- Current runtime targets deterministic correctness over horizontal scalability.

---

## 5. Why NYX Matters
NYX establishes a verifiable, evidence-first foundation for multi-service Web3 portals. New protocols (governance, staking, bridges) can be added without altering the existing evidence schema or enforcement model. This makes NYX suitable as a long-term infrastructure substrate rather than a single application.

