# NYX Operational Readiness (SRE-Grade)

This document defines SLIs/SLOs, monitoring, and incident response.

## 1) SLIs & SLOs (Proposal)

### Gateway API
- **Availability**: 99.9% monthly
- **p95 latency**: < 300ms for read requests, < 800ms for mutations
- **Error rate**: < 0.5% 5xx

### Portal Web
- **Availability**: 99.9% monthly
- **p95 page load**: < 3s on standard broadband

### Evidence Replay
- **Replay success**: ≥ 99.99% of runs

## 2) Logging

- Structured logs with `request_id` and `run_id`
- Redact secrets and avoid logging full payloads
- Separate audit logs from application logs

## 3) Metrics & Tracing

- Metrics exporter: `scripts/nyx_metrics_exporter.py`
- Prometheus/Grafana stack: `deploy/free-tier/monitoring`
- Built-in `/metrics` endpoints:
  - Gateway: `http://<gateway-host>:8091/metrics`
  - Evidence backend: `http://<backend-host>:8090/metrics`

### Metrics Catalog (Prometheus)
Gateway (nyx-backend-gateway):
- `nyx_gateway_http_requests_total{method,path,status}` — counter
- `nyx_gateway_http_request_latency_seconds{method,path}` — histogram (seconds)
- `nyx_gateway_http_errors_total{method,path,code}` — counter
- `nyx_gateway_db_query_total{operation}` — counter
- `nyx_gateway_db_query_seconds{operation}` — histogram (seconds)
- `nyx_gateway_evidence_seconds{module,action}` — histogram (seconds)

Evidence backend (nyx-backend):
- `nyx_backend_http_requests_total{method,path,status}` — counter
- `nyx_backend_http_request_latency_seconds{method,path}` — histogram (seconds)
- `nyx_backend_http_errors_total{method,path,code}` — counter
- `nyx_backend_evidence_seconds{module,action}` — histogram (seconds)

### Tracing (OpenTelemetry)
- Enable spans with `NYX_OTEL_ENABLED=true`.
- Current exporter is stdout (dev-safe). In production, route to an OTEL collector.

## 4) Alerts (Minimum)

- Gateway health check failures
- DB integrity failures
- Evidence replay failures
- Negative balances or abnormal transfer spikes
- Web2 guard errors > threshold

## 4.1) Risk Controls & Circuit Breakers

- 风控入口：`docs/MAINNET_RISK_CONTROLS.md`
- 建议生产默认 `NYX_RISK_MODE=enforce`
- 熔断触发应联动告警（错误爆发/异常金额）

## 5) Incident Response

- **P1**: gateway down, evidence replay failure, or integrity failure
- **P2**: partial outages (e.g., Web2 guard failure)
- **P3**: degraded performance

Runbook references:
- `docs/OPS_RUNBOOK_FREE_TIER.md`
- `docs/DEPLOYMENT_FREE_TIER.md`

## 6) Backup / Restore / DR

- Daily encrypted backups (AES‑256‑GCM + PBKDF2)
- Weekly restore drills
- RPO: 24 hours (minimum)
- RTO: 4 hours (minimum)

## 7) Capacity & Scaling

- Single-node default (free tier)
- Scale by separating gateway + DB + web hosting
- Use read replicas or snapshots for evidence archive

## 8) On-Call & Auditability

- Maintain on-call rotation for production
- Retain evidence logs for audit windows

## 9) Runbooks

### 9.1 Rolling restart (gateway)
1. Verify `/healthz` is green on all instances.
2. Restart one instance at a time.
3. Confirm `/healthz` and `/version` on the restarted instance.
4. Repeat for the next instance.

### 9.2 Database migrations
- `create_connection()` auto-applies schema migrations on startup.
- **Before upgrades**: take a backup (see `scripts/nyx_backup_encrypted.sh`).
- **After upgrades**: verify DB schema version and run `scripts/nyx_verify_all.sh`.

### 9.3 Rollback
1. Stop the gateway process.
2. Restore the latest encrypted backup (`scripts/nyx_restore_encrypted.sh`).
3. Redeploy the previous release artifact.
4. Verify `/healthz`, `/capabilities`, and evidence replay.
