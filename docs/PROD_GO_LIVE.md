# NYX Production Go‑Live Checklist (Mainnet-Equivalent)

This document defines **non‑negotiable** production requirements for a mainnet‑equivalent launch. Testnet releases may run with reduced scope, but **production must satisfy every item** below.

## 1) Key Replacement + Secrets Management
- **MUST** replace all dev/test keys listed in `PUBLIC_KEYS_AND_REPLACEMENTS.md`.
- **MUST** store keys in a secrets manager (CI/CD or cloud KMS) with least‑privilege access.
- **MUST** rotate keys before launch and on every security incident.
- **MUST NOT** commit production keys to git, CI logs, or client bundles.

## 2) KYC/AML + Compliance
- **MUST** select a KYC/AML vendor and define jurisdictional coverage.
- **MUST** implement sanctions screening + transaction monitoring for mainnet flows.
- **MUST** implement review/appeal workflow for flagged accounts.
- **MUST** define data retention + deletion windows aligned to legal counsel.
- **MUST** log compliance decisions without storing sensitive PII in plaintext.
- Templates: `docs/MAINNET_COMPLIANCE_TEMPLATE.md`, `docs/LEGAL_TEMPLATES_MAINNET.md`

## 3) Privacy Policy + Terms of Service
- **MUST** publish a Privacy Policy covering data collection, processing, and retention.
- **MUST** publish Terms of Service covering user obligations, prohibited conduct, and dispute resolution.
- **MUST** provide a contact channel for privacy/abuse requests.
- **MUST** include explicit disclosures for on‑chain/public data visibility.
- Templates: `docs/LEGAL_TEMPLATES_MAINNET.md`

## 4) Logging + Redaction
- **MUST** redact secrets (API keys, tokens, signatures, raw ciphertext) from logs.
- **MUST** avoid logging full wallet addresses when not required (hash/shorten in logs).
- **MUST** tag every request with a request_id/run_id for traceability.
- **MUST** separate audit logs from application logs with restricted access.

## 5) Monitoring + Alerting
- **MUST** monitor API latency, error rates, and 5xx spikes.
- **MUST** monitor DB health (connections, replication lag, disk).
- **MUST** monitor wallet operations (unexpected drain, spikes, failed transfers).
- **MUST** alert on replay verification failures and evidence generation errors.
- **MUST** keep an incident runbook with on-call escalation.
  - Baseline (free) implemented: `scripts/nyx_monitor_local.py`, `scripts/nyx_metrics_exporter.py` + `docs/OPS_RUNBOOK_FREE_TIER.md`.

## 6) Backup + Disaster Recovery
- **MUST** snapshot DB daily and retain at least 30 days.
- **MUST** test restore procedures at least monthly.
- **MUST** define RPO/RTO targets for API and evidence storage.
- **MUST** store backups encrypted at rest and in a separate account/project.
  - Baseline (free, strong encryption) implemented: `scripts/nyx_backup_encrypted.sh`, `scripts/nyx_restore_encrypted.sh`.

## 7) Security Review + Penetration Testing
- **MUST** run dependency/SAST scans on every release candidate.
- **MUST** complete a third‑party penetration test before mainnet.
- **MUST** review evidence pipeline for tamper resistance and leakage.
- **MUST** document security findings and remediation timelines.

## 8) App Store / Enterprise Distribution
- **MUST** maintain Apple developer certificates and device provisioning.
- **MUST** document App Store submission checklist (privacy labels, encryption export).
- **MUST** support enterprise/internal signing flow if applicable.
- **MUST** verify that the iOS app’s WebView policies match compliance requirements.

## 9) Mainnet Configuration + Risk Controls
- **MUST** validate chain IDs, RPC endpoints, and network fee models.
- **MUST** define fee schedule (protocol + platform) and treasury routing.
- **MUST** implement risk limits (per‑account, per‑IP, per‑day).
- **MUST** separate hot/cold wallets with multi‑sig for cold storage.
- **MUST** provide circuit‑breaker toggles for trading, swap, and purchase flows.
- Risk config: `docs/MAINNET_RISK_CONTROLS.md`

## 10) Web2 Guard Production Requirements
- **MUST** maintain a tight allowlist with explicit host + path_prefix rules.
- **MUST** hash request/response content and store only hashes in evidence.
- **MUST NOT** store raw API keys or secrets in the backend.
- **MUST** log allowlist expansions and approvals.

---

### Current Testnet Status
- Testnet runs with deterministic receipts + evidence.
- Production controls above are **required before mainnet**, even if testnet passes.

### Sign‑off (Draft)
- Owner: **Huangjiahao**
- Date: **2026‑02‑05**
