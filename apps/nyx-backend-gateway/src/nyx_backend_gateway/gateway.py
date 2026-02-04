from __future__ import annotations

from dataclasses import dataclass
import hashlib
import ipaddress
import json
import os
import re
import socket
import ssl
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from nyx_backend_gateway.env import (
    get_faucet_cooldown_seconds,
    get_faucet_ip_max_claims_per_24h,
    get_faucet_max_amount_per_24h,
    get_faucet_max_claims_per_24h,
    get_fee_address,
)
from nyx_backend_gateway.exchange import ExchangeError, cancel_order, place_order
from nyx_backend_gateway.fees import route_fee
from nyx_backend_gateway.storage import (
    AirdropClaim,
    EvidenceRun,
    EntertainmentEvent,
    EntertainmentItem,
    FeeLedger,
    Listing,
    MessageEvent,
    Order,
    Purchase,
    Receipt,
    Web2GuardRequest,
    apply_wallet_faucet,
    apply_wallet_faucet_with_fee,
    apply_wallet_transfer,
    create_connection,
    insert_airdrop_claim,
    insert_faucet_claim,
    insert_entertainment_event,
    insert_entertainment_item,
    insert_evidence_run,
    insert_fee_ledger,
    insert_listing,
    insert_message_event,
    insert_purchase,
    insert_receipt,
    insert_web2_guard_request,
    get_wallet_balance,
    list_listings,
    list_web2_guard_requests,
    load_by_id,
    FaucetClaim,
)


class GatewayError(ValueError):
    pass


class GatewayApiError(GatewayError):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        http_status: int = 400,
        details: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.http_status = http_status
        self.details = details or {}


@dataclass(frozen=True)
class GatewayResult:
    run_id: str
    state_hash: str
    receipt_hashes: list[str]
    replay_ok: bool


_MAX_AMOUNT = 1_000_000
_MAX_PRICE = 1_000_000
_ENTERTAINMENT_MODES = {"pulse", "drift", "scan"}
_ADDRESS_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_SUPPORTED_ASSETS: dict[str, dict[str, object]] = {
    "NYXT": {"name": "NYX Testnet Token"},
    "ECHO": {"name": "Echo Test Asset"},
    "USDX": {"name": "NYX Testnet Stable"},
}

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

_AIRDROP_TASKS_V1: list[dict[str, object]] = [
    {
        "task_id": "trade_1",
        "title": "Complete 1 trade",
        "description": "Get an order filled on NYXT/ECHO.",
        "reward": 250,
    },
    {
        "task_id": "chat_1",
        "title": "Send 1 E2EE DM",
        "description": "Send one encrypted DM message.",
        "reward": 100,
    },
    {
        "task_id": "store_1",
        "title": "Buy 1 item",
        "description": "Complete one marketplace purchase.",
        "reward": 200,
    },
]


def list_airdrop_tasks_v1(conn, account_id: str) -> list[dict[str, object]]:
    acct = _validate_address_text(account_id, "account_id")

    claimed_rows = conn.execute(
        "SELECT task_id, reward, created_at, run_id FROM airdrop_claims WHERE account_id = ?",
        (acct,),
    ).fetchall()
    claimed: dict[str, dict[str, object]] = {}
    for row in claimed_rows:
        task_id = str(row["task_id"])
        claimed[task_id] = {
            "task_id": task_id,
            "reward": int(row["reward"]),
            "created_at": int(row["created_at"]),
            "run_id": str(row["run_id"]),
        }

    trade_row = conn.execute(
        "SELECT o.run_id AS run_id FROM trades t "
        "JOIN orders o ON o.order_id = t.order_id "
        "WHERE o.owner_address = ? "
        "ORDER BY t.trade_id ASC LIMIT 1",
        (acct,),
    ).fetchone()
    trade_run_id = str(trade_row["run_id"]) if trade_row is not None else None

    chat_row = conn.execute(
        "SELECT run_id FROM messages WHERE sender_account_id = ? ORDER BY message_id ASC LIMIT 1",
        (acct,),
    ).fetchone()
    chat_run_id = str(chat_row["run_id"]) if chat_row is not None else None

    store_row = conn.execute(
        "SELECT run_id FROM purchases WHERE buyer_id = ? ORDER BY purchase_id ASC LIMIT 1",
        (acct,),
    ).fetchone()
    store_run_id = str(store_row["run_id"]) if store_row is not None else None

    completion_run_ids: dict[str, str | None] = {
        "trade_1": trade_run_id,
        "chat_1": chat_run_id,
        "store_1": store_run_id,
    }

    out: list[dict[str, object]] = []
    for task in _AIRDROP_TASKS_V1:
        task_id = str(task["task_id"])
        completion_run_id = completion_run_ids.get(task_id)
        completed = completion_run_id is not None
        claim_record = claimed.get(task_id)
        claimed_flag = claim_record is not None
        out.append(
            {
                "task_id": task_id,
                "title": str(task["title"]),
                "description": str(task["description"]),
                "reward": int(task["reward"]),
                "completed": completed,
                "completion_run_id": completion_run_id,
                "claimed": claimed_flag,
                "claim_run_id": str(claim_record["run_id"]) if claim_record is not None else None,
                "claimable": bool(completed and not claimed_flag),
            }
        )
    return out


def execute_airdrop_claim_v1(
    *,
    seed: int,
    run_id: str,
    account_id: str,
    payload: dict[str, Any],
    db_path: Path | None = None,
    run_root: Path | None = None,
) -> tuple[GatewayResult, int, FeeLedger, dict[str, object]]:
    acct = _validate_address_text(account_id, "account_id")
    if not isinstance(payload, dict):
        raise GatewayApiError("PAYLOAD_INVALID", "payload must be object", http_status=400)
    task_id = payload.get("task_id")
    if not isinstance(task_id, str) or not task_id or isinstance(task_id, bool):
        raise GatewayApiError("TASK_ID_REQUIRED", "task_id required", http_status=400)
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,32}", task_id):
        raise GatewayApiError("TASK_ID_INVALID", "task_id invalid", http_status=400)

    task_map = {str(t["task_id"]): t for t in _AIRDROP_TASKS_V1}
    task = task_map.get(task_id)
    if task is None:
        raise GatewayApiError("TASK_UNKNOWN", "task_id not supported", http_status=404, details={"task_id": task_id})
    reward = int(task["reward"])

    conn = create_connection(db_path or _db_path())
    try:
        existing = conn.execute(
            "SELECT run_id FROM airdrop_claims WHERE account_id = ? AND task_id = ?",
            (acct, task_id),
        ).fetchone()
        if existing is not None:
            raise GatewayApiError(
                "TASK_ALREADY_CLAIMED",
                "airdrop already claimed",
                http_status=409,
                details={"task_id": task_id, "claim_run_id": str(existing["run_id"])},
            )

        completion_run_id: str | None = None
        if task_id == "trade_1":
            row = conn.execute(
                "SELECT o.run_id AS run_id FROM trades t "
                "JOIN orders o ON o.order_id = t.order_id "
                "WHERE o.owner_address = ? "
                "ORDER BY t.trade_id ASC LIMIT 1",
                (acct,),
            ).fetchone()
            completion_run_id = str(row["run_id"]) if row is not None else None
        if task_id == "chat_1":
            row = conn.execute(
                "SELECT run_id FROM messages WHERE sender_account_id = ? ORDER BY message_id ASC LIMIT 1",
                (acct,),
            ).fetchone()
            completion_run_id = str(row["run_id"]) if row is not None else None
        if task_id == "store_1":
            row = conn.execute(
                "SELECT run_id FROM purchases WHERE buyer_id = ? ORDER BY purchase_id ASC LIMIT 1",
                (acct,),
            ).fetchone()
            completion_run_id = str(row["run_id"]) if row is not None else None

        if completion_run_id is None:
            raise GatewayApiError(
                "TASK_INCOMPLETE",
                "task not completed yet",
                http_status=409,
                details={"task_id": task_id},
            )

        claim_payload = {"address": acct, "task_id": task_id, "reward": reward, "completion_run_id": completion_run_id}
        fee_record = route_fee("wallet", "airdrop", claim_payload, run_id)

        backend_src = _backend_src()
        if str(backend_src) not in __import__("sys").path:
            __import__("sys").path.insert(0, str(backend_src))
        from nyx_backend.evidence import EvidenceError, run_evidence

        run_root = run_root or _run_root()
        try:
            evidence = run_evidence(
                seed=seed,
                run_id=run_id,
                module="wallet",
                action="airdrop",
                payload=claim_payload,
                base_dir=run_root,
            )
        except EvidenceError as exc:
            raise GatewayError(str(exc)) from exc

        insert_evidence_run(
            conn,
            EvidenceRun(
                run_id=run_id,
                module="wallet",
                action="airdrop",
                seed=seed,
                state_hash=evidence.state_hash,
                receipt_hashes=evidence.receipt_hashes,
                replay_ok=evidence.replay_ok,
            ),
        )
        insert_receipt(
            conn,
            Receipt(
                receipt_id=_receipt_id(run_id),
                module="wallet",
                action="airdrop",
                state_hash=evidence.state_hash,
                receipt_hashes=evidence.receipt_hashes,
                replay_ok=evidence.replay_ok,
                run_id=run_id,
            ),
        )

        result = apply_wallet_faucet_with_fee(
            conn,
            address=acct,
            amount=reward,
            fee_total=fee_record.total_paid,
            treasury_address=fee_record.fee_address,
            run_id=run_id,
            asset_id="NYXT",
        )
        insert_fee_ledger(conn, fee_record)
        insert_airdrop_claim(
            conn,
            AirdropClaim(
                claim_id=_deterministic_id("airdrop-claim", run_id),
                account_id=acct,
                task_id=task_id,
                reward=reward,
                created_at=int(time.time()),
                run_id=run_id,
            ),
        )
        conn.commit()
        return (
            GatewayResult(
                run_id=run_id,
                state_hash=evidence.state_hash,
                receipt_hashes=evidence.receipt_hashes,
                replay_ok=evidence.replay_ok,
            ),
            int(result["balance"]),
            fee_record,
            {"task_id": task_id, "reward": reward, "completion_run_id": completion_run_id},
        )
    finally:
        conn.close()


def _entertainment_items() -> list[EntertainmentItem]:
    return [
        EntertainmentItem(
            item_id="ent-001",
            title="Signal Drift",
            summary="Deterministic state steps for testnet alpha.",
            category="pulse",
        ),
        EntertainmentItem(
            item_id="ent-002",
            title="Echo Field",
            summary="Bounded steps with stable evidence output.",
            category="drift",
        ),
        EntertainmentItem(
            item_id="ent-003",
            title="Arc Loop",
            summary="Preview-only loop with deterministic receipts.",
            category="scan",
        ),
    ]


def _ensure_entertainment_items(conn) -> None:
    for item in _entertainment_items():
        insert_entertainment_item(conn, item)


def _repo_root() -> Path:
    path = Path(__file__).resolve()
    for _ in range(5):
        path = path.parent
    return path


def _backend_src() -> Path:
    return _repo_root() / "apps" / "nyx-backend" / "src"


def _run_root() -> Path:
    root = _repo_root() / "apps" / "nyx-backend-gateway" / "runs"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _db_path() -> Path:
    override = os.environ.get("NYX_GATEWAY_DB_PATH", "").strip()
    if override:
        path = Path(override).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        return path
    data_dir = _repo_root() / "apps" / "nyx-backend-gateway" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "nyx_gateway.db"


def _deterministic_id(prefix: str, run_id: str) -> str:
    digest = hashlib.sha256(f"{prefix}:{run_id}".encode("utf-8")).hexdigest()
    return f"{prefix}-{digest[:16]}"


def _order_id(run_id: str) -> str:
    return _deterministic_id("order", run_id)


def _receipt_id(run_id: str) -> str:
    return _deterministic_id("receipt", run_id)


def _require_text(payload: dict[str, Any], key: str, max_len: int = 64) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value or isinstance(value, bool):
        raise GatewayError(f"{key} required")
    if len(value) > max_len:
        raise GatewayError(f"{key} too long")
    return value


def _require_url(payload: dict[str, Any], key: str = "url") -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value or isinstance(value, bool):
        raise GatewayApiError("PARAM_REQUIRED", f"{key} required", http_status=400, details={"param": key})
    raw = value.strip()
    if len(raw) > _WEB2_MAX_URL_LEN:
        raise GatewayApiError("PARAM_INVALID", f"{key} too long", http_status=400, details={"param": key})
    if any(ch.isspace() for ch in raw):
        raise GatewayApiError("PARAM_INVALID", f"{key} invalid", http_status=400, details={"param": key})
    return raw


def _require_web2_method(payload: dict[str, Any]) -> str:
    raw = payload.get("method", "GET")
    if not isinstance(raw, str) or isinstance(raw, bool):
        raise GatewayApiError("PARAM_INVALID", "method invalid", http_status=400, details={"param": "method"})
    method = raw.strip().upper()
    if method not in _WEB2_ALLOWED_METHODS:
        raise GatewayApiError("PARAM_INVALID", "method not allowed", http_status=400, details={"param": "method"})
    return method


def _coerce_web2_body(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str) and not isinstance(value, bool):
        text = value
    elif isinstance(value, (dict, list)):
        text = json.dumps(value, sort_keys=True, separators=(",", ":"))
    else:
        raise GatewayApiError("PARAM_INVALID", "body must be text or json", http_status=400, details={"param": "body"})
    raw = text.encode("utf-8")
    if len(raw) > _WEB2_MAX_BODY_BYTES:
        raise GatewayApiError(
            "PARAM_INVALID",
            "body too large",
            http_status=400,
            details={"param": "body", "limit_bytes": _WEB2_MAX_BODY_BYTES},
        )
    return text


def _coerce_sealed_request(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or isinstance(value, bool):
        raise GatewayApiError("PARAM_INVALID", "sealed_request invalid", http_status=400, details={"param": "sealed_request"})
    if len(value) > _WEB2_MAX_SEALED_LEN:
        raise GatewayApiError(
            "PARAM_INVALID",
            "sealed_request too large",
            http_status=400,
            details={"param": "sealed_request", "limit": _WEB2_MAX_SEALED_LEN},
        )
    return value


def _require_address(payload: dict[str, Any], key: str) -> str:
    value = _require_text(payload, key, max_len=64)
    if not _ADDRESS_PATTERN.fullmatch(value):
        raise GatewayError(f"{key} invalid")
    return value


def _validate_address_text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value or isinstance(value, bool):
        raise GatewayError(f"{name} required")
    if len(value) > 64:
        raise GatewayError(f"{name} too long")
    if not _ADDRESS_PATTERN.fullmatch(value):
        raise GatewayError(f"{name} invalid")
    return value


def _require_amount(payload: dict[str, Any], key: str = "amount", max_value: int = _MAX_AMOUNT) -> int:
    value = payload.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise GatewayError(f"{key} must be int")
    if value <= 0 or value > max_value:
        raise GatewayError(f"{key} out of bounds")
    return value


def _validate_wallet_transfer(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise GatewayError("payload must be object")
    from_address = _require_address(payload, "from_address")
    to_address = _require_address(payload, "to_address")
    if from_address == to_address:
        raise GatewayError("addresses must differ")
    amount = _require_amount(payload, "amount")
    asset_id = _require_asset_id(payload, "asset_id")
    return {
        "from_address": from_address,
        "to_address": to_address,
        "amount": amount,
        "asset_id": asset_id,
    }


def _validate_wallet_faucet(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise GatewayError("payload must be object")
    address = _require_address(payload, "address")
    amount = _require_amount(payload, "amount", max_value=10_000)
    asset_id = _require_asset_id(payload, "asset_id")
    return {
        "address": address,
        "amount": amount,
        "asset_id": asset_id,
    }


def _require_token(payload: dict[str, Any], key: str = "token") -> str:
    token = payload.get(key, "NYXT")
    if not isinstance(token, str) or not token or isinstance(token, bool):
        raise GatewayError("token invalid")
    if token != "NYXT":
        raise GatewayError("token unsupported")
    return token


def _require_asset_id(payload: dict[str, Any], key: str = "asset_id") -> str:
    raw = payload.get(key, "NYXT")
    if not isinstance(raw, str) or not raw or isinstance(raw, bool):
        raise GatewayError("asset_id invalid")
    asset_id = raw.strip().upper()
    if asset_id not in _SUPPORTED_ASSETS:
        raise GatewayError("asset_id unsupported")
    return asset_id


def _require_int(payload: dict[str, Any], key: str, min_value: int = 1, max_value: int | None = None) -> int:
    value = payload.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise GatewayError(f"{key} must be int")
    if value < min_value:
        raise GatewayError(f"{key} out of bounds")
    if max_value is not None and value > max_value:
        raise GatewayError(f"{key} too large")
    return value


def _validate_exchange_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "asset_in": _require_text(payload, "asset_in"),
        "asset_out": _require_text(payload, "asset_out"),
        "amount": _require_int(payload, "amount", 1, _MAX_AMOUNT),
        "min_out": _require_int(payload, "min_out", 1, _MAX_PRICE),
    }


def _validate_place_order(payload: dict[str, Any]) -> dict[str, Any]:
    side = _require_text(payload, "side", max_len=8).upper()
    if side not in {"BUY", "SELL"}:
        raise GatewayError("side must be BUY or SELL")
    asset_in = _require_asset_id(payload, "asset_in")
    asset_out = _require_asset_id(payload, "asset_out")
    if asset_in == asset_out:
        raise GatewayError("asset_out must differ")
    # Testnet v1: only the NYXT/ECHO pair is supported (mainnet-equivalent UX, fewer pairs).
    if side == "BUY" and (asset_in, asset_out) != ("NYXT", "ECHO"):
        raise GatewayError("pair unsupported")
    if side == "SELL" and (asset_in, asset_out) != ("ECHO", "NYXT"):
        raise GatewayError("pair unsupported")
    return {
        "owner_address": _require_address(payload, "owner_address"),
        "side": side,
        "asset_in": asset_in,
        "asset_out": asset_out,
        "amount": _require_int(payload, "amount", 1, _MAX_AMOUNT),
        "price": _require_int(payload, "price", 1, _MAX_PRICE),
    }


def _validate_cancel(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "order_id": _require_text(payload, "order_id"),
    }


def _validate_chat_payload(payload: dict[str, Any]) -> dict[str, Any]:
    channel = _require_text(payload, "channel")
    message = _require_text(payload, "message", max_len=2048)
    # Enforce E2EE ciphertext envelope (backend stores ciphertext only).
    try:
        parsed = json.loads(message)
    except json.JSONDecodeError as exc:
        raise GatewayError("message must be e2ee json") from exc
    if not isinstance(parsed, dict):
        raise GatewayError("message must be e2ee json")
    if not isinstance(parsed.get("ciphertext"), str) or not parsed.get("ciphertext"):
        raise GatewayError("message missing ciphertext")
    if not isinstance(parsed.get("iv"), str) or not parsed.get("iv"):
        raise GatewayError("message missing iv")
    return {"channel": channel, "message": message}


def _validate_market_payload(payload: dict[str, Any]) -> dict[str, Any]:
    sku = _require_text(payload, "sku")
    title = _require_text(payload, "title", max_len=120)
    price = _require_int(payload, "price", 1, _MAX_PRICE)
    qty = _require_int(payload, "qty", 1, _MAX_AMOUNT)
    return {"sku": sku, "title": title, "price": price, "qty": qty}


def _validate_listing_payload(payload: dict[str, Any]) -> dict[str, Any]:
    sku = _require_text(payload, "sku")
    title = _require_text(payload, "title", max_len=120)
    price = _require_int(payload, "price", 1, _MAX_PRICE)
    return {
        "publisher_id": _require_address(payload, "publisher_id"),
        "sku": sku,
        "title": title,
        "price": price,
    }


def _validate_purchase_payload(payload: dict[str, Any]) -> dict[str, Any]:
    listing_id = _require_text(payload, "listing_id")
    qty = _require_int(payload, "qty", 1, _MAX_AMOUNT)
    return {
        "buyer_id": _require_address(payload, "buyer_id"),
        "listing_id": listing_id,
        "qty": qty,
    }


def _validate_entertainment_payload(payload: dict[str, Any]) -> dict[str, Any]:
    item_id = _require_text(payload, "item_id", max_len=32)
    mode = _require_text(payload, "mode", max_len=32)
    if mode not in _ENTERTAINMENT_MODES:
        raise GatewayError("mode not allowed")
    step = _require_int(payload, "step", 0, 20)
    return {"item_id": item_id, "mode": mode, "step": step}


def list_web2_allowlist() -> list[dict[str, object]]:
    return [
        {
            "id": entry["id"],
            "label": entry["label"],
            "base_url": entry["base_url"],
            "path_prefix": entry["path_prefix"],
            "methods": sorted(entry["methods"]),
        }
        for entry in _WEB2_ALLOWLIST
    ]


def _web2_hash_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _web2_request_hash(method: str, url: str, body: str, allowlist_id: str) -> str:
    payload = json.dumps(
        {"method": method, "url": url, "body": body, "allowlist_id": allowlist_id},
        sort_keys=True,
        separators=(",", ":"),
    )
    return _web2_hash_bytes(payload.encode("utf-8"))


def _web2_match_allowlist(url: str, method: str) -> dict[str, object]:
    parsed = urlparse(url)
    if parsed.scheme.lower() != "https":
        raise GatewayApiError("ALLOWLIST_DENY", "https required", http_status=400, details={"url": url})
    if parsed.username or parsed.password:
        raise GatewayApiError("ALLOWLIST_DENY", "url userinfo not allowed", http_status=400)
    if parsed.port is not None:
        raise GatewayApiError("ALLOWLIST_DENY", "custom port not allowed", http_status=400)
    host = (parsed.hostname or "").lower()
    if not host:
        raise GatewayApiError("ALLOWLIST_DENY", "host required", http_status=400)
    try:
        ipaddress.ip_address(host)
        raise GatewayApiError("ALLOWLIST_DENY", "ip host not allowed", http_status=400)
    except ValueError:
        pass
    path = parsed.path or "/"
    for entry in _WEB2_ALLOWLIST:
        if host != entry["host"]:
            continue
        if not path.startswith(str(entry["path_prefix"])):
            continue
        if method not in entry["methods"]:
            raise GatewayApiError(
                "ALLOWLIST_DENY",
                "method not allowed for host",
                http_status=400,
                details={"host": host, "method": method},
            )
        return entry
    raise GatewayApiError("ALLOWLIST_DENY", "url not allowlisted", http_status=400, details={"host": host})


def _web2_headers(method: str) -> dict[str, str]:
    headers = {
        "User-Agent": "NYX-Web2-Guard/1.0",
        "Accept": "application/json",
    }
    if method == "POST":
        headers["Content-Type"] = "application/json"
    return headers


def _web2_normalized_url(url: str, allow_entry: dict[str, object]) -> str:
    parsed = urlparse(url)
    path = parsed.path or "/"
    if not path.startswith("/"):
        path = f"/{path}"
    query = f"?{parsed.query}" if parsed.query else ""
    base = str(allow_entry["base_url"]).rstrip("/")
    return f"{base}{path}{query}"


def _web2_request(
    *,
    url: str,
    method: str,
    body: str,
) -> tuple[int, bytes, bool, str | None]:
    headers = _web2_headers(method)
    data = body.encode("utf-8") if method == "POST" and body else None
    request = Request(url, headers=headers, data=data, method=method)
    error_hint: str | None = None

    try:
        with urlopen(request, timeout=_WEB2_TIMEOUT_SECONDS, context=ssl.create_default_context()) as resp:
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


def execute_run(
    *,
    seed: int,
    run_id: str,
    module: str,
    action: str,
    payload: dict[str, Any] | None,
    caller_account_id: str | None = None,
    db_path: Path | None = None,
    run_root: Path | None = None,
) -> GatewayResult:
    if payload is None:
        payload = {}

    if module == "marketplace" and action == "order_intent":
        raise GatewayError("action not supported")
    
    # Verify ownership for state-mutating actions
    if module == "exchange" and action == "place_order":
        payload = _validate_place_order(payload)
        if caller_account_id and payload.get("owner_address") != caller_account_id:
            raise GatewayError("owner_address mismatch")
    if module == "exchange" and action == "cancel_order":
        payload = _validate_cancel(payload)
        # TODO: Verify order ownership in DB
    if module == "chat" and action == "message_event":
        payload = _validate_chat_payload(payload)
        # Note: Chat messages are tied to the caller via post_message logic
    if module == "marketplace" and action == "purchase_listing":
        if not caller_account_id:
            raise GatewayError("auth required")
        payload = _validate_purchase_payload(payload)
        if caller_account_id and payload.get("buyer_id") != caller_account_id:
            raise GatewayError("buyer_id mismatch")
    if module == "marketplace" and action == "listing_publish":
        if not caller_account_id:
            raise GatewayError("auth required")
        payload = _validate_listing_payload(payload)
        if caller_account_id and payload.get("publisher_id") != caller_account_id:
            raise GatewayError("publisher_id mismatch")

    backend_src = _backend_src()
    if str(backend_src) not in __import__("sys").path:
        __import__("sys").path.insert(0, str(backend_src))

    from nyx_backend.evidence import EvidenceError, run_evidence

    run_root = run_root or _run_root()
    try:
        evidence = run_evidence(
            seed=seed,
            run_id=run_id,
            module=module,
            action=action,
            payload=payload,
            base_dir=run_root,
        )
    except EvidenceError as exc:
        raise GatewayError(str(exc)) from exc

    conn = create_connection(db_path or _db_path())
    insert_evidence_run(
        conn,
        EvidenceRun(
            run_id=run_id,
            module=module,
            action=action,
            seed=seed,
            state_hash=evidence.state_hash,
            receipt_hashes=evidence.receipt_hashes,
            replay_ok=evidence.replay_ok,
        ),
    )
    insert_receipt(
        conn,
        Receipt(
            receipt_id=_receipt_id(run_id),
            module=module,
            action=action,
            state_hash=evidence.state_hash,
            receipt_hashes=evidence.receipt_hashes,
            replay_ok=evidence.replay_ok,
            run_id=run_id,
        ),
    )

    fee_record: FeeLedger | None = None
    if module == "exchange" and action in {"route_swap", "place_order", "cancel_order"}:
        fee_record = route_fee(module, action, payload, run_id)
        insert_fee_ledger(conn, fee_record)
    if module == "marketplace" and action in {"listing_publish", "purchase_listing"}:
        fee_record = route_fee(module, action, payload, run_id)
        insert_fee_ledger(conn, fee_record)
    if module == "chat" and action == "message_event":
        fee_record = route_fee(module, action, payload, run_id)

    if module == "exchange" and action == "place_order":
        if fee_record is not None and caller_account_id:
            nyxt_balance = get_wallet_balance(conn, caller_account_id, "NYXT")
            required = int(fee_record.total_paid)
            if payload.get("asset_in") == "NYXT":
                required += int(payload.get("amount", 0) or 0)
            if nyxt_balance < required:
                raise GatewayError("insufficient NYXT balance for amount + fee")
        order = Order(
            order_id=_order_id(run_id),
            owner_address=payload["owner_address"],
            side=payload["side"],
            amount=payload["amount"],
            price=payload["price"],
            asset_in=payload["asset_in"],
            asset_out=payload["asset_out"],
            run_id=run_id,
        )
        try:
            place_order(conn, order)
        except ExchangeError as exc:
            raise GatewayError(str(exc)) from exc
    if module == "exchange" and action == "cancel_order":
        try:
            if caller_account_id:
                record = load_by_id(conn, "orders", "order_id", payload["order_id"])
                if record is None:
                    raise GatewayError("order_id not found")
                if str(record.get("owner_address")) != caller_account_id:
                    raise GatewayError("order_id ownership mismatch")
                if str(record.get("status") or "open") != "open":
                    raise GatewayError("order not cancellable")
            cancel_order(conn, payload["order_id"])
        except ExchangeError as exc:
            raise GatewayError(str(exc)) from exc
    if fee_record is not None and module == "exchange" and action in {"place_order", "cancel_order"}:
        if not caller_account_id:
            raise GatewayError("auth required")
        apply_wallet_transfer(
            conn,
            transfer_id=_deterministic_id("fee", run_id),
            from_address=caller_account_id,
            to_address=fee_record.fee_address,
            asset_id="NYXT",
            amount=0,
            fee_total=fee_record.total_paid,
            treasury_address=fee_record.fee_address,
            run_id=run_id,
        )

    if module == "chat" and action == "message_event":
        if not caller_account_id:
            raise GatewayError("auth required")
        if fee_record is not None:
            nyxt_balance = get_wallet_balance(conn, caller_account_id, "NYXT")
            if nyxt_balance < int(fee_record.total_paid):
                raise GatewayError("insufficient NYXT balance for fee")
            apply_wallet_transfer(
                conn,
                transfer_id=_deterministic_id("fee", run_id),
                from_address=caller_account_id,
                to_address=fee_record.fee_address,
                asset_id="NYXT",
                amount=0,
                fee_total=fee_record.total_paid,
                treasury_address=fee_record.fee_address,
                run_id=run_id,
            )
            insert_fee_ledger(conn, fee_record)
        insert_message_event(
            conn,
            MessageEvent(
                message_id=_deterministic_id("message", run_id),
                channel=payload["channel"],
                sender_account_id=caller_account_id,
                body=payload["message"],
                run_id=run_id,
            ),
        )
    if module == "marketplace" and action == "listing_publish":
        if fee_record is not None and caller_account_id:
            nyxt_balance = get_wallet_balance(conn, caller_account_id, "NYXT")
            if nyxt_balance < int(fee_record.total_paid):
                raise GatewayError("insufficient NYXT balance for fee")
        insert_listing(
            conn,
            Listing(
                listing_id=_deterministic_id("listing", run_id),
                publisher_id=payload["publisher_id"],
                sku=payload["sku"],
                title=payload["title"],
                price=payload["price"],
                status="active",
                run_id=run_id,
            ),
        )
        if fee_record is not None and caller_account_id:
            apply_wallet_transfer(
                conn,
                transfer_id=_deterministic_id("fee", run_id),
                from_address=caller_account_id,
                to_address=fee_record.fee_address,
                asset_id="NYXT",
                amount=0,
                fee_total=fee_record.total_paid,
                treasury_address=fee_record.fee_address,
                run_id=run_id,
            )
    if module == "marketplace" and action == "purchase_listing":
        listing_record = load_by_id(conn, "listings", "listing_id", payload["listing_id"])
        if listing_record is None:
            raise GatewayError("listing_id not found")
        if str(listing_record.get("status") or "active") != "active":
            raise GatewayError("listing not available")
        
        # Real logic: Transfer funds
        total_price = int(listing_record["price"]) * int(payload["qty"])
        if fee_record is not None and caller_account_id:
            nyxt_balance = get_wallet_balance(conn, caller_account_id, "NYXT")
            required = total_price + int(fee_record.total_paid)
            if nyxt_balance < required:
                raise GatewayError("insufficient NYXT balance for amount + fee")
        apply_wallet_transfer(
            conn,
            transfer_id=_deterministic_id("purchase-xfer", run_id),
            from_address=payload["buyer_id"],
            to_address=str(listing_record["publisher_id"]),
            asset_id="NYXT",
            amount=total_price,
            fee_total=int(fee_record.total_paid) if fee_record is not None else 0,
            treasury_address=fee_record.fee_address if fee_record is not None else get_fee_address(),
            run_id=run_id
        )
        
        insert_purchase(
            conn,
            Purchase(
                purchase_id=_deterministic_id("purchase", run_id),
                listing_id=payload["listing_id"],
                buyer_id=payload["buyer_id"],
                qty=payload["qty"],
                run_id=run_id,
            ),
        )
        # Mark listing as sold for simplicity
        conn.execute("UPDATE listings SET status = 'sold' WHERE listing_id = ?", (payload["listing_id"],))
        conn.commit()
    if module == "entertainment" and action == "state_step":
        _ensure_entertainment_items(conn)
        item_record = load_by_id(conn, "entertainment_items", "item_id", payload["item_id"])
        if item_record is None:
            raise GatewayError("item_id not found")
        insert_entertainment_event(
            conn,
            EntertainmentEvent(
                event_id=_deterministic_id("ent-event", run_id),
                item_id=payload["item_id"],
                mode=payload["mode"],
                step=payload["step"],
                run_id=run_id,
            ),
        )
    if module == "dapp" and action == "sign_request":
        # Record dapp interaction as evidence
        conn.execute(
            "INSERT INTO message_events (message_id, channel, body, run_id) VALUES (?, ?, ?, ?)",
            (_deterministic_id("dapp-sig", run_id), payload["dapp_url"], f"Signed: {payload['method']}", run_id)
        )

    conn.close()

    return GatewayResult(
        run_id=run_id,
        state_hash=evidence.state_hash,
        receipt_hashes=evidence.receipt_hashes,
        replay_ok=evidence.replay_ok,
    )


def execute_wallet_transfer(
    *,
    seed: int,
    run_id: str,
    payload: dict[str, Any],
    db_path: Path | None = None,
    run_root: Path | None = None,
) -> tuple[GatewayResult, dict[str, int], FeeLedger]:
    validated = _validate_wallet_transfer(payload)
    asset_id = validated.get("asset_id", "NYXT")
    fee_record = route_fee("wallet", "transfer", validated, run_id)
    conn = create_connection(db_path or _db_path())
    
    from_balance = get_wallet_balance(conn, validated["from_address"], asset_id)
    nyxt_balance = get_wallet_balance(conn, validated["from_address"], "NYXT")
    
    if asset_id == "NYXT":
        if nyxt_balance < (validated["amount"] + fee_record.total_paid):
            raise GatewayError("insufficient balance for amount + fee")
    else:
        if from_balance < validated["amount"]:
            raise GatewayError(f"insufficient {asset_id} balance")
        if nyxt_balance < fee_record.total_paid:
            raise GatewayError("insufficient NYXT balance for fee")

    backend_src = _backend_src()
    if str(backend_src) not in __import__("sys").path:
        __import__("sys").path.insert(0, str(backend_src))
    from nyx_backend.evidence import EvidenceError, run_evidence

    run_root = run_root or _run_root()
    try:
        evidence = run_evidence(
            seed=seed,
            run_id=run_id,
            module="wallet",
            action="transfer",
            payload=validated,
            base_dir=run_root,
        )
    except EvidenceError as exc:
        raise GatewayError(str(exc)) from exc

    insert_evidence_run(
        conn,
        EvidenceRun(
            run_id=run_id,
            module="wallet",
            action="transfer",
            seed=seed,
            state_hash=evidence.state_hash,
            receipt_hashes=evidence.receipt_hashes,
            replay_ok=evidence.replay_ok,
        ),
    )
    insert_receipt(
        conn,
        Receipt(
            receipt_id=_receipt_id(run_id),
            module="wallet",
            action="transfer",
            state_hash=evidence.state_hash,
            receipt_hashes=evidence.receipt_hashes,
            replay_ok=evidence.replay_ok,
            run_id=run_id,
        ),
    )
    balances = apply_wallet_transfer(
        conn,
        transfer_id=_deterministic_id("wallet", run_id),
        from_address=validated["from_address"],
        to_address=validated["to_address"],
        asset_id=asset_id,
        amount=validated["amount"],
        fee_total=fee_record.total_paid,
        treasury_address=fee_record.fee_address,
        run_id=run_id,
    )
    insert_fee_ledger(conn, fee_record)
    return (
        GatewayResult(
            run_id=run_id,
            state_hash=evidence.state_hash,
            receipt_hashes=evidence.receipt_hashes,
            replay_ok=evidence.replay_ok,
        ),
        balances,
        fee_record,
    )


def execute_wallet_faucet(
    *,
    seed: int,
    run_id: str,
    payload: dict[str, Any],
    db_path: Path | None = None,
    run_root: Path | None = None,
) -> tuple[GatewayResult, dict[str, int], FeeLedger]:
    validated = _validate_wallet_faucet(payload)
    address = validated["address"]
    amount = int(validated.get("amount", 1000))
    asset_id = validated.get("asset_id", "NYXT")

    fee_record = route_fee("wallet", "faucet", validated, run_id)
    conn = create_connection(db_path or _db_path())
    
    backend_src = _backend_src()
    if str(backend_src) not in __import__("sys").path:
        __import__("sys").path.insert(0, str(backend_src))
    from nyx_backend.evidence import EvidenceError, run_evidence

    run_root = run_root or _run_root()
    try:
        evidence = run_evidence(
            seed=seed,
            run_id=run_id,
            module="wallet",
            action="faucet",
            payload=validated,
            base_dir=run_root,
        )
    except EvidenceError as exc:
        raise GatewayError(str(exc)) from exc

    insert_evidence_run(
        conn,
        EvidenceRun(
            run_id=run_id,
            module="wallet",
            action="faucet",
            seed=seed,
            state_hash=evidence.state_hash,
            receipt_hashes=evidence.receipt_hashes,
            replay_ok=evidence.replay_ok,
        ),
    )
    insert_receipt(
        conn,
        Receipt(
            receipt_id=_receipt_id(run_id),
            module="wallet",
            action="faucet",
            state_hash=evidence.state_hash,
            receipt_hashes=evidence.receipt_hashes,
            replay_ok=evidence.replay_ok,
            run_id=run_id,
        ),
    )
    
    result = apply_wallet_faucet_with_fee(
        conn,
        address=address,
        amount=amount,
        fee_total=fee_record.total_paid,
        treasury_address=fee_record.fee_address,
        run_id=run_id,
        asset_id=asset_id,
    )
    insert_fee_ledger(conn, fee_record)
    
    return (
        GatewayResult(
            run_id=run_id,
            state_hash=evidence.state_hash,
            receipt_hashes=evidence.receipt_hashes,
            replay_ok=evidence.replay_ok,
        ),
        result,
        fee_record,
    )


def execute_wallet_faucet_v1(
    *,
    seed: int,
    run_id: str,
    payload: dict[str, Any],
    account_id: str,
    client_ip: str | None = None,
    db_path: Path | None = None,
    run_root: Path | None = None,
) -> tuple[GatewayResult, int, FeeLedger]:
    validated = _validate_wallet_faucet(payload)
    address = validated["address"]
    if address != account_id:
        raise GatewayApiError(
            "FAUCET_ADDRESS_MISMATCH",
            "address must match authenticated account_id",
            http_status=403,
        )

    ip = (client_ip or "unknown").strip() or "unknown"
    now = int(time.time())
    window_start = now - 24 * 60 * 60
    cooldown = get_faucet_cooldown_seconds()
    max_amount = get_faucet_max_amount_per_24h()
    max_claims = get_faucet_max_claims_per_24h()
    ip_max_claims = get_faucet_ip_max_claims_per_24h()

    conn = create_connection(db_path or _db_path())
    try:
        last_row = conn.execute(
            "SELECT created_at FROM faucet_claims WHERE account_id = ? ORDER BY created_at DESC LIMIT 1",
            (account_id,),
        ).fetchone()
        if last_row is not None and cooldown:
            last_at = int(last_row["created_at"])
            retry_after = cooldown - (now - last_at)
            if retry_after > 0:
                raise GatewayApiError(
                    "FAUCET_COOLDOWN",
                    "faucet cooldown active",
                    http_status=429,
                    details={"retry_after_seconds": retry_after},
                )

        row = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) AS total_amount, COUNT(*) AS claim_count "
            "FROM faucet_claims WHERE account_id = ? AND created_at >= ?",
            (account_id, window_start),
        ).fetchone()
        total_amount = int(row["total_amount"]) if row is not None else 0
        claim_count = int(row["claim_count"]) if row is not None else 0

        if max_claims and claim_count >= max_claims:
            raise GatewayApiError(
                "FAUCET_DAILY_CLAIMS_EXCEEDED",
                "daily faucet claim limit exceeded",
                http_status=429,
                details={"max_claims_per_24h": max_claims},
            )

        requested_amount = int(validated["amount"])
        if max_amount and (total_amount + requested_amount) > max_amount:
            raise GatewayApiError(
                "FAUCET_DAILY_AMOUNT_EXCEEDED",
                "daily faucet amount limit exceeded",
                http_status=429,
                details={
                    "max_amount_per_24h": max_amount,
                    "already_claimed_amount_24h": total_amount,
                },
            )

        ip_row = conn.execute(
            "SELECT COUNT(*) AS claim_count FROM faucet_claims WHERE ip = ? AND created_at >= ?",
            (ip, window_start),
        ).fetchone()
        ip_claim_count = int(ip_row["claim_count"]) if ip_row is not None else 0
        if ip_max_claims and ip_claim_count >= ip_max_claims:
            raise GatewayApiError(
                "FAUCET_IP_LIMIT_EXCEEDED",
                "ip faucet claim limit exceeded",
                http_status=429,
                details={"ip_max_claims_per_24h": ip_max_claims},
            )

        fee_record = route_fee("wallet", "faucet", validated, run_id)

        backend_src = _backend_src()
        if str(backend_src) not in __import__("sys").path:
            __import__("sys").path.insert(0, str(backend_src))
        from nyx_backend.evidence import EvidenceError, run_evidence

        run_root = run_root or _run_root()
        try:
            evidence = run_evidence(
                seed=seed,
                run_id=run_id,
                module="wallet",
                action="faucet",
                payload=validated,
                base_dir=run_root,
            )
        except EvidenceError as exc:
            raise GatewayError(str(exc)) from exc

        insert_evidence_run(
            conn,
            EvidenceRun(
                run_id=run_id,
                module="wallet",
                action="faucet",
                seed=seed,
                state_hash=evidence.state_hash,
                receipt_hashes=evidence.receipt_hashes,
                replay_ok=evidence.replay_ok,
            ),
        )
        insert_receipt(
            conn,
            Receipt(
                receipt_id=_receipt_id(run_id),
                module="wallet",
                action="faucet",
                state_hash=evidence.state_hash,
                receipt_hashes=evidence.receipt_hashes,
                replay_ok=evidence.replay_ok,
                run_id=run_id,
            ),
        )

        faucet_result = apply_wallet_faucet_with_fee(
            conn,
            address=validated["address"],
            amount=requested_amount,
            fee_total=fee_record.total_paid,
            treasury_address=fee_record.fee_address,
            run_id=run_id,
            asset_id=validated["asset_id"],
        )
        insert_fee_ledger(conn, fee_record)
        insert_faucet_claim(
            conn,
            FaucetClaim(
                claim_id=_deterministic_id("faucet-claim", run_id),
                account_id=account_id,
                address=validated["address"],
                asset_id=validated["asset_id"],
                amount=requested_amount,
                ip=ip,
                created_at=now,
                run_id=run_id,
            ),
        )
        conn.commit()
        return (
            GatewayResult(
                run_id=run_id,
                state_hash=evidence.state_hash,
                receipt_hashes=evidence.receipt_hashes,
                replay_ok=evidence.replay_ok,
            ),
            int(faucet_result["balance"]),
            fee_record,
        )
    finally:
        conn.close()


def execute_airdrop_claim(
    *,
    seed: int,
    run_id: str,
    payload: dict[str, Any],
    db_path: Path | None = None,
    run_root: Path | None = None,
) -> tuple[GatewayResult, dict[str, int], FeeLedger]:
    address = str(payload["address"])
    task_id = str(payload["task_id"])
    amount = int(payload["reward"])
    
    fee_record = route_fee("wallet", "airdrop", payload, run_id)
    conn = create_connection(db_path or _db_path())
    
    # Check if already claimed
    existing = conn.execute(
        "SELECT 1 FROM wallet_transfers WHERE to_address = ? AND run_id LIKE ?",
        (address, f"airdrop-{task_id}-%")
    ).fetchone()
    if existing:
        raise GatewayError("Airdrop already claimed for this task")

    backend_src = _backend_src()
    if str(backend_src) not in __import__("sys").path:
        __import__("sys").path.insert(0, str(backend_src))
    from nyx_backend.evidence import EvidenceError, run_evidence

    run_root = run_root or _run_root()
    try:
        evidence = run_evidence(
            seed=seed,
            run_id=run_id,
            module="wallet",
            action="airdrop",
            payload=payload,
            base_dir=run_root,
        )
    except EvidenceError as exc:
        raise GatewayError(str(exc)) from exc

    insert_evidence_run(
        conn,
        EvidenceRun(
            run_id=run_id,
            module="wallet",
            action="airdrop",
            seed=seed,
            state_hash=evidence.state_hash,
            receipt_hashes=evidence.receipt_hashes,
            replay_ok=evidence.replay_ok,
        ),
    )
    
    result = apply_wallet_faucet_with_fee(
        conn,
        address=address,
        amount=amount,
        fee_total=fee_record.total_paid,
        treasury_address=fee_record.fee_address,
        run_id=f"airdrop-{task_id}-{run_id}",
        asset_id="NYXT",
    )
    insert_fee_ledger(conn, fee_record)
    
    return (
        GatewayResult(
            run_id=run_id,
            state_hash=evidence.state_hash,
            receipt_hashes=evidence.receipt_hashes,
            replay_ok=evidence.replay_ok,
        ),
        result,
        fee_record,
    )


def execute_web2_guard_request(
    *,
    seed: int,
    run_id: str,
    payload: dict[str, Any],
    account_id: str,
    db_path: Path | None = None,
    run_root: Path | None = None,
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
    conn = create_connection(db_path or _db_path())
    try:
        balance = get_wallet_balance(conn, account_id, "NYXT")
        if balance < fee_record.total_paid:
            raise GatewayApiError(
                "INSUFFICIENT_BALANCE",
                "insufficient balance for fee",
                http_status=400,
                details={"balance": balance, "required": fee_record.total_paid},
            )

        backend_src = _backend_src()
        if str(backend_src) not in __import__("sys").path:
            __import__("sys").path.insert(0, str(backend_src))
        from nyx_backend.evidence import EvidenceError, run_evidence

        run_root = run_root or _run_root()
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
        try:
            evidence = run_evidence(
                seed=seed,
                run_id=run_id,
                module="web2",
                action="guard_request",
                payload=evidence_payload,
                base_dir=run_root,
            )
        except EvidenceError as exc:
            raise GatewayError(str(exc)) from exc

        insert_evidence_run(
            conn,
            EvidenceRun(
                run_id=run_id,
                module="web2",
                action="guard_request",
                seed=seed,
                state_hash=evidence.state_hash,
                receipt_hashes=evidence.receipt_hashes,
                replay_ok=evidence.replay_ok,
            ),
        )
        insert_receipt(
            conn,
            Receipt(
                receipt_id=_receipt_id(run_id),
                module="web2",
                action="guard_request",
                state_hash=evidence.state_hash,
                receipt_hashes=evidence.receipt_hashes,
                replay_ok=evidence.replay_ok,
                run_id=run_id,
            ),
        )

        balances = apply_wallet_transfer(
            conn,
            transfer_id=_deterministic_id("web2-fee", run_id),
            from_address=account_id,
            to_address=fee_record.fee_address,
            asset_id="NYXT",
            amount=fee_record.total_paid,
            fee_total=0,
            treasury_address=fee_record.fee_address,
            run_id=f"fee-{run_id}",
        )
        insert_fee_ledger(conn, fee_record)

        now = int(time.time())
        insert_web2_guard_request(
            conn,
            Web2GuardRequest(
                request_id=_deterministic_id("web2-req", run_id),
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
    finally:
        conn.close()

    return {
        "run_id": run_id,
        "state_hash": evidence.state_hash,
        "receipt_hashes": evidence.receipt_hashes,
        "replay_ok": evidence.replay_ok,
        "request_id": _deterministic_id("web2-req", run_id),
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


def supported_assets() -> list[dict[str, object]]:
    return [{"asset_id": asset_id, **meta} for asset_id, meta in sorted(_SUPPORTED_ASSETS.items())]


def fetch_wallet_balance(address: str, asset_id: str = "NYXT") -> int:
    conn = create_connection(_db_path())
    balance = get_wallet_balance(conn, address, asset_id)
    conn.close()
    return balance


def fetch_web2_guard_requests(
    *,
    account_id: str,
    limit: int = 50,
    offset: int = 0,
    db_path: Path | None = None,
) -> list[dict[str, object]]:
    conn = create_connection(db_path or _db_path())
    try:
        return list_web2_guard_requests(conn, account_id=account_id, limit=limit, offset=offset)
    finally:
        conn.close()


def marketplace_list_active_listings(conn, limit: int = 100, offset: int = 0) -> list[dict[str, object]]:
    return list_listings(conn, limit=limit, offset=offset)


def marketplace_search_listings(conn, q: str, limit: int = 100, offset: int = 0) -> list[dict[str, object]]:
    query = (q or "").strip()
    if not query:
        return list_listings(conn, limit=limit, offset=offset)
    if len(query) > 64:
        raise GatewayError("q too long")
    lim = int(limit)
    off = int(offset)
    if lim < 1 or lim > 200:
        raise GatewayError("limit out of bounds")
    if off < 0:
        raise GatewayError("offset out of bounds")
    pattern = f"%{query}%"
    rows = conn.execute(
        "SELECT * FROM listings WHERE status = 'active' AND (sku LIKE ? OR title LIKE ?) "
        "ORDER BY listing_id ASC LIMIT ? OFFSET ?",
        (pattern, pattern, lim, off),
    ).fetchall()
    return [{col: row[col] for col in row.keys()} for row in rows]
