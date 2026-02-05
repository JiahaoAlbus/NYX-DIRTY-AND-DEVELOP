#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _default_db_path() -> Path:
    data_dir = _repo_root() / "apps" / "nyx-backend-gateway" / "data"
    return data_dir / "nyx_gateway.db"


def _http_get_json(url: str, timeout: float = 5.0) -> dict[str, Any]:
    req = Request(url, method="GET")
    with urlopen(req, timeout=timeout) as resp:
        data = resp.read()
    return json.loads(data.decode("utf-8"))


def _post_webhook(url: str, payload: dict[str, Any]) -> None:
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    req = Request(url, method="POST", data=body, headers={"content-type": "application/json"})
    with urlopen(req, timeout=5) as resp:
        resp.read()


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def main() -> int:
    base_url = os.environ.get("NYX_MONITOR_BASE_URL", "http://127.0.0.1:8091").strip()
    db_path = Path(os.environ.get("NYX_GATEWAY_DB_PATH", "").strip() or _default_db_path())
    lookback_hours = _env_int("NYX_MONITOR_LOOKBACK_HOURS", 24)
    max_web2_errors = _env_int("NYX_MONITOR_MAX_WEB2_ERRORS", 5)
    max_failed_replay = _env_int("NYX_MONITOR_MAX_FAILED_REPLAY", 0)
    max_negative_balances = _env_int("NYX_MONITOR_MAX_NEGATIVE_BALANCES", 0)
    max_transfer_amount = _env_int("NYX_MONITOR_MAX_TRANSFER_AMOUNT", 1_000_000)
    alert_webhook = os.environ.get("NYX_MONITOR_ALERT_WEBHOOK", "").strip()

    report: dict[str, Any] = {
        "ts": int(time.time()),
        "base_url": base_url,
        "db_path": str(db_path),
        "checks": {},
        "warnings": [],
        "critical": [],
    }

    # API health check
    try:
        health = _http_get_json(f"{base_url}/healthz")
        report["checks"]["healthz"] = health
        if not health.get("ok"):
            report["critical"].append("healthz_not_ok")
    except (URLError, ValueError) as exc:
        report["critical"].append(f"healthz_failed:{exc}")

    # Capabilities check
    try:
        caps = _http_get_json(f"{base_url}/capabilities")
        report["checks"]["capabilities"] = {"modules": caps.get("modules"), "endpoints": len(caps.get("endpoints", []))}
    except (URLError, ValueError) as exc:
        report["warnings"].append(f"capabilities_failed:{exc}")

    if not db_path.exists():
        report["critical"].append("db_missing")
    else:
        try:
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("PRAGMA quick_check")
            integrity = cur.fetchone()[0]
            report["checks"]["db_integrity"] = integrity
            if integrity != "ok":
                report["critical"].append("db_integrity_failed")

            # Negative balances
            cur.execute("SELECT COUNT(*) FROM wallet_accounts WHERE balance < 0")
            neg_bal = cur.fetchone()[0]
            report["checks"]["negative_balances"] = neg_bal
            if neg_bal > max_negative_balances:
                report["critical"].append(f"negative_balances>{max_negative_balances}")

            # Failed evidence replays
            cur.execute("SELECT COUNT(*) FROM evidence_runs WHERE replay_ok = 0")
            failed_replay = cur.fetchone()[0]
            report["checks"]["failed_replay"] = failed_replay
            if failed_replay > max_failed_replay:
                report["critical"].append(f"failed_replay>{max_failed_replay}")

            # Web2 Guard failures (lookback window)
            since_ts = int(time.time() - lookback_hours * 3600)
            cur.execute(
                "SELECT COUNT(*) FROM web2_guard_requests WHERE created_at >= ? AND response_status >= 400",
                (since_ts,),
            )
            web2_errors = cur.fetchone()[0]
            report["checks"]["web2_errors"] = web2_errors
            if web2_errors > max_web2_errors:
                report["warnings"].append(f"web2_errors>{max_web2_errors}")

            # Large transfers (recent by rowid)
            cur.execute("SELECT transfer_id, amount FROM wallet_transfers ORDER BY rowid DESC LIMIT 50")
            large = [row["transfer_id"] for row in cur.fetchall() if int(row["amount"]) > max_transfer_amount]
            report["checks"]["large_transfers"] = large
            if large:
                report["warnings"].append("large_transfers_detected")

            conn.close()
        except Exception as exc:
            report["critical"].append(f"db_check_failed:{exc}")

    status = "ok"
    if report["critical"]:
        status = "critical"
    elif report["warnings"]:
        status = "warning"
    report["status"] = status

    print(json.dumps(report, indent=2, sort_keys=True))

    if alert_webhook and status in {"warning", "critical"}:
        try:
            _post_webhook(alert_webhook, report)
        except Exception:
            pass

    return 1 if status == "critical" else 0


if __name__ == "__main__":
    raise SystemExit(main())
