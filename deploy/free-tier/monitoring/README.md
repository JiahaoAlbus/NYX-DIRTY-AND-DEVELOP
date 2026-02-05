# NYX Free-Tier Monitoring (Prometheus + Grafana)

This folder provides a **zero-cost monitoring panel** for NYX using Prometheus + Grafana.

## 1) Prerequisites
- Docker + Docker Compose
- NYX backend running on `127.0.0.1:8091`
- Metrics exporter running on `127.0.0.1:9099` (`python scripts/nyx_metrics_exporter.py`)

## 2) Start the stack

```bash
export GRAFANA_ADMIN_PASSWORD="your-strong-password"
docker compose -f deploy/free-tier/monitoring/docker-compose.yml up -d
```

Grafana: `http://localhost:3000`  
Prometheus: `http://localhost:9090`

Default Grafana user: `admin`  
Password: `${GRAFANA_ADMIN_PASSWORD}`

## 3) Linux note

The compose file uses `host.docker.internal`. On Linux, the `extra_hosts` line maps it to `host-gateway` (Docker 20.10+).

## 4) Dashboards

The stack automatically provisions:
- Datasource: Prometheus
- Dashboard: **NYX Overview**

If you want custom dashboards, drop JSON files into:
`deploy/free-tier/monitoring/grafana/dashboards/`
