#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _default_db_path() -> Path:
    data_dir = _repo_root() / "apps" / "nyx-backend-gateway" / "data"
    return data_dir / "nyx_gateway.db"


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _http_get_json(url: str, timeout: float = 3.0) -> dict[str, Any]:
    req = Request(url, method="GET")
    with urlopen(req, timeout=timeout) as resp:
        data = resp.read()
    return json.loads(data.decode("utf-8"))


def _table_present(conn: sqlite3.Connection, table: str) -> bool:
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name = ?", (table,))
    return cur.fetchone() is not None


def _query_scalar(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> int:
    cur = conn.execute(sql, params)
    row = cur.fetchone()
    if row is None:
        return 0
    value = row[0]
    if value is None:
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


class MetricsCache:
    def __init__(self, db_path: Path, base_url: str, cache_seconds: int, timeout: float) -> None:
        self.db_path = db_path
        self.base_url = base_url
        self.cache_seconds = cache_seconds
        self.timeout = timeout
        self._lock = threading.Lock()
        self._last_ts = 0.0
        self._cache: dict[str, Any] = {}

    def get(self) -> dict[str, Any]:
        now = time.time()
        with self._lock:
            if now - self._last_ts > self.cache_seconds:
                self._cache = self._collect()
                self._last_ts = now
            return dict(self._cache)

    def _collect(self) -> dict[str, Any]:
        start = time.time()
        metrics: dict[str, Any] = {
            "ts": int(time.time()),
            "db_path": str(self.db_path),
            "base_url": self.base_url,
            "gauges": {},
            "series": [],
            "errors": [],
        }

        gauges = metrics["gauges"]
        series = metrics["series"]

        gauges["nyx_metrics_up"] = 1
        gauges["nyx_metrics_cache_seconds"] = self.cache_seconds

        # API health check
        health_ok = 0
        health_latency_ms = 0
        try:
            t0 = time.time()
            health = _http_get_json(f"{self.base_url}/healthz", timeout=self.timeout)
            health_ok = 1 if health.get("ok") else 0
            health_latency_ms = int((time.time() - t0) * 1000)
        except (URLError, ValueError, TimeoutError) as exc:
            metrics["errors"].append(f"healthz_failed:{exc}")
        gauges["nyx_api_health_ok"] = health_ok
        gauges["nyx_api_health_latency_ms"] = health_latency_ms

        if not self.db_path.exists():
            metrics["errors"].append("db_missing")
            gauges["nyx_db_present"] = 0
        else:
            gauges["nyx_db_present"] = 1
            gauges["nyx_db_size_bytes"] = self.db_path.stat().st_size
            try:
                conn = sqlite3.connect(str(self.db_path))
                conn.row_factory = sqlite3.Row
                integrity = conn.execute("PRAGMA quick_check").fetchone()[0]
                gauges["nyx_db_integrity_ok"] = 1 if integrity == "ok" else 0

                def table_flag(name: str) -> bool:
                    present = _table_present(conn, name)
                    series.append(
                        {
                            "name": "nyx_table_present",
                            "labels": {"table": name},
                            "value": 1 if present else 0,
                        }
                    )
                    return present

                if table_flag("wallet_accounts"):
                    gauges["nyx_wallet_accounts_total"] = _query_scalar(conn, "SELECT COUNT(*) FROM wallet_accounts")
                    gauges["nyx_wallet_accounts_negative"] = _query_scalar(
                        conn, "SELECT COUNT(*) FROM wallet_accounts WHERE balance < 0"
                    )
                    gauges["nyx_wallet_balance_total"] = _query_scalar(
                        conn, "SELECT COALESCE(SUM(balance), 0) FROM wallet_accounts"
                    )

                if table_flag("wallet_transfers"):
                    gauges["nyx_wallet_transfers_total"] = _query_scalar(conn, "SELECT COUNT(*) FROM wallet_transfers")
                    gauges["nyx_wallet_transfer_amount_total"] = _query_scalar(
                        conn, "SELECT COALESCE(SUM(amount), 0) FROM wallet_transfers"
                    )
                    gauges["nyx_wallet_transfer_fee_total"] = _query_scalar(
                        conn, "SELECT COALESCE(SUM(fee_total), 0) FROM wallet_transfers"
                    )

                if table_flag("faucet_claims"):
                    gauges["nyx_faucet_claims_total"] = _query_scalar(conn, "SELECT COUNT(*) FROM faucet_claims")
                    since_ts = int(time.time() - 24 * 3600)
                    gauges["nyx_faucet_claims_24h"] = _query_scalar(
                        conn, "SELECT COUNT(*) FROM faucet_claims WHERE created_at >= ?", (since_ts,)
                    )

                if table_flag("airdrop_claims"):
                    gauges["nyx_airdrop_claims_total"] = _query_scalar(conn, "SELECT COUNT(*) FROM airdrop_claims")

                if table_flag("orders"):
                    gauges["nyx_exchange_orders_total"] = _query_scalar(conn, "SELECT COUNT(*) FROM orders")
                    for status in ("open", "filled", "cancelled"):
                        count = _query_scalar(conn, "SELECT COUNT(*) FROM orders WHERE status = ?", (status,))
                        series.append(
                            {"name": "nyx_exchange_orders", "labels": {"status": status}, "value": count}
                        )

                if table_flag("trades"):
                    gauges["nyx_exchange_trades_total"] = _query_scalar(conn, "SELECT COUNT(*) FROM trades")

                if table_flag("listings"):
                    gauges["nyx_store_listings_total"] = _query_scalar(conn, "SELECT COUNT(*) FROM listings")
                    for status in ("active", "inactive"):
                        count = _query_scalar(conn, "SELECT COUNT(*) FROM listings WHERE status = ?", (status,))
                        series.append(
                            {"name": "nyx_store_listings", "labels": {"status": status}, "value": count}
                        )

                if table_flag("purchases"):
                    gauges["nyx_store_purchases_total"] = _query_scalar(conn, "SELECT COUNT(*) FROM purchases")

                if table_flag("receipts"):
                    gauges["nyx_receipts_total"] = _query_scalar(conn, "SELECT COUNT(*) FROM receipts")
                    gauges["nyx_receipts_replay_failed"] = _query_scalar(
                        conn, "SELECT COUNT(*) FROM receipts WHERE replay_ok = 0"
                    )

                if table_flag("evidence_runs"):
                    gauges["nyx_evidence_runs_total"] = _query_scalar(conn, "SELECT COUNT(*) FROM evidence_runs")
                    gauges["nyx_evidence_runs_failed"] = _query_scalar(
                        conn, "SELECT COUNT(*) FROM evidence_runs WHERE replay_ok = 0"
                    )

                if table_flag("fee_ledger"):
                    gauges["nyx_fee_entries_total"] = _query_scalar(conn, "SELECT COUNT(*) FROM fee_ledger")
                    gauges["nyx_fee_total_paid"] = _query_scalar(
                        conn, "SELECT COALESCE(SUM(total_paid), 0) FROM fee_ledger"
                    )

                if table_flag("portal_accounts"):
                    gauges["nyx_portal_accounts_total"] = _query_scalar(conn, "SELECT COUNT(*) FROM portal_accounts")

                if table_flag("portal_sessions"):
                    gauges["nyx_portal_sessions_total"] = _query_scalar(conn, "SELECT COUNT(*) FROM portal_sessions")

                if table_flag("chat_rooms"):
                    gauges["nyx_chat_rooms_total"] = _query_scalar(conn, "SELECT COUNT(*) FROM chat_rooms")

                if table_flag("chat_messages"):
                    gauges["nyx_chat_messages_total"] = _query_scalar(conn, "SELECT COUNT(*) FROM chat_messages")
                    since_ts = int(time.time() - 24 * 3600)
                    gauges["nyx_chat_messages_24h"] = _query_scalar(
                        conn, "SELECT COUNT(*) FROM chat_messages WHERE created_at >= ?", (since_ts,)
                    )

                if table_flag("messages"):
                    gauges["nyx_legacy_messages_total"] = _query_scalar(conn, "SELECT COUNT(*) FROM messages")

                if table_flag("web2_guard_requests"):
                    gauges["nyx_web2_guard_requests_total"] = _query_scalar(
                        conn, "SELECT COUNT(*) FROM web2_guard_requests"
                    )
                    since_ts = int(time.time() - 24 * 3600)
                    gauges["nyx_web2_guard_errors_24h"] = _query_scalar(
                        conn,
                        "SELECT COUNT(*) FROM web2_guard_requests WHERE created_at >= ? AND response_status >= 400",
                        (since_ts,),
                    )

                conn.close()
            except Exception as exc:
                metrics["errors"].append(f"db_query_failed:{exc}")

        gauges["nyx_metrics_error_count"] = len(metrics["errors"])
        gauges["nyx_metrics_scrape_duration_ms"] = int((time.time() - start) * 1000)
        return metrics


def _format_labels(labels: dict[str, str]) -> str:
    if not labels:
        return ""
    items = ",".join(f'{key}="{value}"' for key, value in labels.items())
    return f"{{{items}}}"


class MetricsHandler(BaseHTTPRequestHandler):
    cache: MetricsCache

    def _write_json(self, payload: dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _write_text(self, body: str, status: int = 200) -> None:
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "text/plain; version=0.0.4")
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802
        metrics = self.cache.get()
        if self.path == "/metrics.json":
            return self._write_json(metrics)
        if self.path == "/healthz":
            ok = 1 if metrics.get("gauges", {}).get("nyx_db_present") else 0
            payload = {"ok": bool(ok), "ts": metrics.get("ts"), "errors": metrics.get("errors", [])}
            return self._write_json(payload)
        if self.path != "/metrics":
            return self._write_text("not found\n", status=404)

        lines: list[str] = []
        for name, value in sorted(metrics.get("gauges", {}).items()):
            lines.append(f"{name} {value}")
        for item in metrics.get("series", []):
            label_str = _format_labels(item.get("labels", {}))
            lines.append(f"{item.get('name')}{label_str} {item.get('value')}")
        self._write_text("\n".join(lines) + "\n")

    def log_message(self, format: str, *args: Any) -> None:
        if os.environ.get("NYX_METRICS_SILENT", "1") == "1":
            return
        super().log_message(format, *args)


def main() -> int:
    listen = os.environ.get("NYX_METRICS_LISTEN", "127.0.0.1").strip()
    port = _env_int("NYX_METRICS_PORT", 9099)
    cache_seconds = _env_int("NYX_METRICS_CACHE_SECONDS", 10)
    timeout = _env_float("NYX_METRICS_TIMEOUT", 3.0)
    base_url = os.environ.get("NYX_METRICS_BASE_URL", "http://127.0.0.1:8091").strip()
    db_path = Path(os.environ.get("NYX_GATEWAY_DB_PATH", "").strip() or _default_db_path())

    cache = MetricsCache(db_path=db_path, base_url=base_url, cache_seconds=cache_seconds, timeout=timeout)
    MetricsHandler.cache = cache

    server = ThreadingHTTPServer((listen, port), MetricsHandler)
    print(f"NYX metrics exporter listening on http://{listen}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
