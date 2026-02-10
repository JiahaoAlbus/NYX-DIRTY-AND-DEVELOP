from __future__ import annotations

import json
import time
import urllib.request

from nyx_backend_gateway.env import (
    get_compliance_enabled,
    get_compliance_fail_closed,
    get_compliance_timeout_seconds,
    get_compliance_url,
)
from nyx_backend_gateway.errors import GatewayApiError


def require_clearance(
    *,
    account_id: str | None,
    wallet_address: str | None,
    module: str,
    action: str,
    run_id: str,
    metadata: dict[str, object] | None = None,
) -> dict[str, object]:
    if not get_compliance_enabled():
        return {"status": "skipped"}

    if not account_id or not wallet_address:
        raise GatewayApiError("COMPLIANCE_AUTH_REQUIRED", "compliance requires authenticated identity", http_status=401)

    url = get_compliance_url()
    if not url:
        raise GatewayApiError("COMPLIANCE_CONFIG_MISSING", "compliance url not configured", http_status=500)

    payload = {
        "account_id": account_id,
        "wallet_address": wallet_address,
        "module": module,
        "action": action,
        "run_id": run_id,
        "timestamp": int(time.time()),
        "metadata": metadata or {},
    }
    body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    timeout = get_compliance_timeout_seconds()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        data = json.loads(raw) if raw else {}
        decision = str(data.get("decision") or data.get("status") or "").lower()
        if decision in {"allow", "approved", "ok"}:
            return {"status": "ok", "decision": decision}
        raise GatewayApiError(
            "COMPLIANCE_BLOCKED",
            "compliance decision blocked",
            http_status=403,
            details={"decision": decision or "deny"},
        )
    except GatewayApiError:
        raise
    except Exception as exc:
        if get_compliance_fail_closed():
            raise GatewayApiError(
                "COMPLIANCE_UNAVAILABLE",
                "compliance service unavailable",
                http_status=503,
                details={"error": str(exc)},
            ) from exc
        return {"status": "unavailable", "error": str(exc)}
