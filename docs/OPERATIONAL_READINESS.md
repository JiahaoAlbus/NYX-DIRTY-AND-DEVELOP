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
- Add tracing (OpenTelemetry) when moving to production

## 4) Alerts (Minimum)

- Gateway health check failures
- DB integrity failures
- Evidence replay failures
- Negative balances or abnormal transfer spikes
- Web2 guard errors > threshold

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
