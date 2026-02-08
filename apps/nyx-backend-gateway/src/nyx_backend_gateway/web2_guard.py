from __future__ import annotations

import hashlib
import ipaddress
import json
import logging
import socket
import ssl
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlparse
from urllib.request import HTTPRedirectHandler, HTTPSHandler, Request, build_opener

from nyx_backend_gateway.errors import GatewayApiError, GatewayError
from nyx_backend_gateway.evidence_adapter import run_and_record
from nyx_backend_gateway.fees import route_fee
from nyx_backend_gateway.identifiers import deterministic_id
from nyx_backend_gateway.paths import db_path as default_db_path, run_root as default_run_root
from nyx_backend_gateway.storage import (
    Web2GuardRequest,
    apply_wallet_transfer,
    create_connection,
    get_wallet_balance,
    insert_fee_ledger,
    insert_web2_guard_request,
    list_web2_guard_requests,
)


_WEB2_ALLOWLIST: list[dict[str, object]] = [
    {
        "id": "github",
        "label": "GitHub API",
        "base_url": "https://api.github.com",
        "host": "api.github.com",
        "path_prefix": "/",
        "methods": {"GET"},
    },
    {
        "id": "0x-ethereum",
        "label": "0x Swap API (Ethereum)",
        "base_url": "https://api.0x.org",
        "host": "api.0x.org",
        "path_prefix": "/swap",
        "methods": {"GET"},
    },
    {
        "id": "jupiter",
        "label": "Jupiter Swap API",
        "base_url": "https://api.jup.ag/swap/v1",
        "host": "api.jup.ag",
        "path_prefix": "/swap/v1",
        "methods": {"GET"},
    },
    {
        "id": "magiceden-solana",
        "label": "Magic Eden Solana API",
        "base_url": "https://api-mainnet.magiceden.dev/v2",
        "host": "api-mainnet.magiceden.dev",
        "path_prefix": "/v2",
        "methods": {"GET"},
    },
    {
        "id": "magiceden-evm",
        "label": "Magic Eden EVM API",
        "base_url": "https://api-mainnet.magiceden.dev/v4/evm-public",
        "host": "api-mainnet.magiceden.dev",
        "path_prefix": "/v4/evm-public",
        "methods": {"GET"},
    },
    {
        "id": "coingecko",
        "label": "CoinGecko API",
        "base_url": "https://api.coingecko.com/api/v3",
        "host": "api.coingecko.com",
        "path_prefix": "/api/v3",
        "methods": {"GET"},
    },
    {
        "id": "coincap",
        "label": "CoinCap API",
        "base_url": "https://api.coincap.io/v2",
        "host": "api.coincap.io",
        "path_prefix": "/v2",
        "methods": {"GET"},
    },
    {
        "id": "httpbin",
        "label": "HttpBin",
        "base_url": "https://httpbin.org",
        "host": "httpbin.org",
        "path_prefix": "/",
        "methods": {"GET", "POST"},
    },
]

_WEB2_MAX_URL_LEN = 256
_WEB2_MAX_BODY_BYTES = 2_048
_WEB2_MAX_RESPONSE_BYTES = 100_000
_WEB2_TIMEOUT_SECONDS = 8
_WEB2_MAX_SEALED_LEN = 4_096
_WEB2_ALLOWED_METHODS = {"GET", "POST"}
_logger = logging.getLogger("nyx.web2_guard")


def list_web2_allowlist() -> list[dict[str, object]]:
    return [
        {
            "id": entry["id"],
            "label": entry["label"],
            "base_url": entry["base_url"],
            "methods": sorted(entry["methods"]),
        }
        for entry in _WEB2_ALLOWLIST
    ]


def _require_url(payload: dict[str, Any], key: str = "url") -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value or isinstance(value, bool):
        raise GatewayApiError("PARAM_REQUIRED", f"{key} required", http_status=400, details={"param": key})
    url = value.strip()
    if len(url) > _WEB2_MAX_URL_LEN:
        raise GatewayApiError("PARAM_INVALID", "url too long", http_status=400, details={"param": key})
    return url


def _require_web2_method(payload: dict[str, Any]) -> str:
    value = payload.get("method")
    if not isinstance(value, str) or not value or isinstance(value, bool):
        raise GatewayApiError("PARAM_INVALID", "method invalid", http_status=400, details={"param": "method"})
    method = value.strip().upper()
    if method not in _WEB2_ALLOWED_METHODS:
        raise GatewayApiError("PARAM_INVALID", "method not allowed", http_status=400, details={"param": "method"})
    return method


def _coerce_web2_body(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, (bytes, bytearray)):
        value = value.decode("utf-8", errors="replace")
    if isinstance(value, str):
        body = value
    else:
        try:
            body = json.dumps(value, separators=(",", ":"))
        except TypeError as exc:
            raise GatewayApiError(
                "PARAM_INVALID",
                "body must be text or json",
                http_status=400,
                details={"param": "body"},
            ) from exc
    if len(body.encode("utf-8")) > _WEB2_MAX_BODY_BYTES:
        raise GatewayApiError("PARAM_INVALID", "body too large", http_status=400, details={"param": "body"})
    return body


def _coerce_sealed_request(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        sealed = value.strip()
    else:
        raise GatewayApiError("PARAM_INVALID", "sealed_request invalid", http_status=400, details={"param": "sealed_request"})
    if len(sealed) > _WEB2_MAX_SEALED_LEN:
        raise GatewayApiError("PARAM_INVALID", "sealed_request too long", http_status=400, details={"param": "sealed_request"})
    return sealed


def _web2_hash_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _web2_request_hash(method: str, url: str, body: str, allowlist_id: str) -> str:
    digest = hashlib.sha256(f"{allowlist_id}:{method}:{url}:{body}".encode("utf-8")).hexdigest()
    return digest


def _web2_match_allowlist(url: str, method: str) -> dict[str, object]:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise GatewayApiError("ALLOWLIST_DENY", "https required", http_status=400, details={"url": url})
    if parsed.username or parsed.password:
        raise GatewayApiError("ALLOWLIST_DENY", "url userinfo not allowed", http_status=400)
    if parsed.port is not None and parsed.port not in {443}:
        raise GatewayApiError("ALLOWLIST_DENY", "custom port not allowed", http_status=400)
    if not parsed.hostname:
        raise GatewayApiError("ALLOWLIST_DENY", "host required", http_status=400)

    hostname = parsed.hostname.lower()
    normalized_path = unquote(parsed.path)
    path_segments = [segment for segment in normalized_path.split("/") if segment]
    if any(segment == ".." for segment in path_segments):
        raise GatewayApiError("ALLOWLIST_DENY", "path traversal not allowed", http_status=400)
    try:
        ipaddress.ip_address(hostname)
        raise GatewayApiError("ALLOWLIST_DENY", "ip host not allowed", http_status=400)
    except ValueError:
        pass

    for entry in _WEB2_ALLOWLIST:
        if hostname != entry["host"]:
            continue
        if not parsed.path.startswith(str(entry["path_prefix"])):
            continue
        if method not in entry["methods"]:
            continue
        _web2_resolve_public_host(hostname)
        return entry
    raise GatewayApiError("ALLOWLIST_DENY", "host not allowlisted", http_status=400, details={"host": hostname})


def _web2_headers(method: str) -> dict[str, str]:
    headers = {
        "User-Agent": "NYX-Web2Guard/1.0",
        "Accept": "application/json",
    }
    if method == "POST":
        headers["Content-Type"] = "application/json"
    return headers


def _web2_normalized_url(url: str, allow_entry: dict[str, object]) -> str:
    parsed = urlparse(url)
    safe_url = f"https://{allow_entry['host']}{parsed.path}"
    if parsed.query:
        safe_url = f"{safe_url}?{parsed.query}"
    return safe_url


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[override]
        raise URLError("redirect_not_allowed")


def _web2_resolve_public_host(hostname: str) -> None:
    try:
        infos = socket.getaddrinfo(
            hostname,
            443,
            proto=socket.IPPROTO_TCP,
        )
    except socket.gaierror as exc:
        raise GatewayApiError(
            "ALLOWLIST_DENY",
            "host resolution failed",
            http_status=400,
            details={"host": hostname},
        ) from exc
    if not infos:
        raise GatewayApiError("ALLOWLIST_DENY", "host resolution failed", http_status=400, details={"host": hostname})
    for info in infos:
        ip_str = info[4][0]
        ip = ipaddress.ip_address(ip_str)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved or ip.is_unspecified:
            raise GatewayApiError(
                "ALLOWLIST_DENY",
                "host resolves to private ip",
                http_status=400,
                details={"host": hostname},
            )


def _web2_request(*, url: str, method: str, body: str) -> tuple[int, bytes, bool, str | None]:
    headers = _web2_headers(method)
    data = body.encode("utf-8") if method == "POST" and body else None
    request = Request(url, headers=headers, data=data, method=method)
    error_hint: str | None = None

    try:
        ctx = ssl.create_default_context()
        opener = build_opener(HTTPSHandler(context=ctx), _NoRedirect())
        with opener.open(request, timeout=_WEB2_TIMEOUT_SECONDS) as resp:
            status = int(getattr(resp, "status", 200))
            raw = resp.read(_WEB2_MAX_RESPONSE_BYTES + 1)
    except HTTPError as exc:
        status = int(exc.code)
        raw = exc.read(_WEB2_MAX_RESPONSE_BYTES + 1)
        error_hint = f"http_{status}"
    except URLError as exc:
        reason = getattr(exc, "reason", None)
        if isinstance(reason, socket.timeout):
            error_hint = "timeout"
        elif isinstance(reason, str) and reason == "redirect_not_allowed":
            error_hint = "redirect"
        else:
            error_hint = "unavailable"
        status = 0
        raw = b""
    except socket.timeout:
        error_hint = "timeout"
        status = 0
        raw = b""

    truncated = False
    if len(raw) > _WEB2_MAX_RESPONSE_BYTES:
        truncated = True
        raw = raw[:_WEB2_MAX_RESPONSE_BYTES]
    return status, raw, truncated, error_hint


def execute_web2_guard_request(
    *,
    seed: int,
    run_id: str,
    payload: dict[str, Any],
    account_id: str,
    db_path=None,
    run_root=None,
) -> dict[str, object]:
    if not account_id:
        raise GatewayApiError("AUTH_REQUIRED", "auth required", http_status=401)
    if not isinstance(payload, dict):
        raise GatewayApiError("PARAM_INVALID", "payload must be object", http_status=400)

    url = _require_url(payload, "url")
    method = _require_web2_method(payload)
    body_text = _coerce_web2_body(payload.get("body"))
    sealed_request = _coerce_sealed_request(payload.get("sealed_request"))

    if method == "GET" and body_text:
        raise GatewayApiError("PARAM_INVALID", "body not allowed for GET", http_status=400, details={"param": "body"})

    allow_entry = _web2_match_allowlist(url, method)
    allowlist_id = str(allow_entry["id"])
    safe_url = _web2_normalized_url(url, allow_entry)
    request_hash = _web2_request_hash(method, safe_url, body_text, allowlist_id)

    status, response_bytes, truncated, error_hint = _web2_request(url=safe_url, method=method, body=body_text)
    response_hash = _web2_hash_bytes(response_bytes)
    response_size = len(response_bytes)
    body_size = len(body_text.encode("utf-8")) if body_text else 0
    response_text = response_bytes.decode("utf-8", errors="replace")
    if len(response_text) > 2000:
        response_text = response_text[:2000] + "…"

    fee_record = route_fee("web2", "guard_request", {"amount": 1}, run_id)
    conn = create_connection(db_path or default_db_path())
    try:
        balance = get_wallet_balance(conn, account_id, "NYXT")
        if balance < fee_record.total_paid:
            raise GatewayApiError(
                "INSUFFICIENT_BALANCE",
                "insufficient balance for fee",
                http_status=400,
                details={"balance": balance, "required": fee_record.total_paid},
            )

        evidence_payload = {
            "url": safe_url,
            "method": method,
            "allowlist_id": allowlist_id,
            "request_hash": request_hash,
            "response_hash": response_hash,
            "response_status": status,
            "response_size": response_size,
            "response_truncated": truncated,
            "body_size": body_size,
            "upstream_error": error_hint or "",
        }
        outcome = run_and_record(
            seed=seed,
            run_id=run_id,
            module="web2",
            action="guard_request",
            payload=evidence_payload,
            conn=conn,
            base_dir=run_root or default_run_root(),
        )

        balances = apply_wallet_transfer(
            conn,
            transfer_id=deterministic_id("web2-fee", run_id),
            from_address=account_id,
            to_address=fee_record.fee_address,
            asset_id="NYXT",
            amount=0,
            fee_total=fee_record.total_paid,
            treasury_address=fee_record.fee_address,
            run_id=run_id,
        )
        insert_fee_ledger(conn, fee_record)

        now = int(time.time())
        insert_web2_guard_request(
            conn,
            Web2GuardRequest(
                request_id=deterministic_id("web2-req", run_id),
                account_id=account_id,
                run_id=run_id,
                url=safe_url,
                method=method,
                request_hash=request_hash,
                response_hash=response_hash,
                response_status=status,
                response_size=response_size,
                response_truncated=truncated,
                body_size=body_size,
                header_names=sorted(_web2_headers(method).keys()),
                sealed_request=sealed_request,
                created_at=now,
            ),
        )
        _logger.info(
            "web2_guard_request",
            extra={
                "account_id": account_id,
                "allowlist_id": allowlist_id,
                "request_hash": request_hash,
                "response_hash": response_hash,
                "response_status": status,
                "response_size": response_size,
                "response_truncated": truncated,
                "upstream_error": error_hint or "",
            },
        )
    finally:
        conn.close()

    return {
        "run_id": run_id,
        "state_hash": outcome.state_hash,
        "receipt_hashes": outcome.receipt_hashes,
        "replay_ok": outcome.replay_ok,
        "request_id": deterministic_id("web2-req", run_id),
        "request_hash": request_hash,
        "response_hash": response_hash,
        "response_status": status,
        "response_size": response_size,
        "response_truncated": truncated,
        "body_size": body_size,
        "upstream_ok": bool(status and 200 <= status < 300 and not error_hint),
        "upstream_error": error_hint,
        "response_preview": response_text,
        "fee_total": fee_record.total_paid,
        "fee_breakdown": {
            "protocol_fee_total": fee_record.protocol_fee_total,
            "platform_fee_amount": fee_record.platform_fee_amount,
        },
        "treasury_address": fee_record.fee_address,
        "from_balance": balances["from_balance"],
        "treasury_balance": balances["treasury_balance"],
    }


def fetch_web2_guard_requests(*, account_id: str, limit: int = 50, offset: int = 0, db_path=None) -> list[dict[str, object]]:
    conn = create_connection(db_path or default_db_path())
    try:
        return list_web2_guard_requests(conn, account_id=account_id, limit=limit, offset=offset)
    finally:
        conn.close()
