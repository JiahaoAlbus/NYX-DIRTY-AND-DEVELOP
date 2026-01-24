from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Any

from nyx_backend_gateway.storage import (
    EvidenceRun,
    Listing,
    MessageEvent,
    Order,
    Purchase,
    Receipt,
    Trade,
    create_connection,
    insert_evidence_run,
    insert_listing,
    insert_message_event,
    insert_order,
    insert_purchase,
    insert_receipt,
    insert_trade,
)


class GatewayError(ValueError):
    pass


@dataclass(frozen=True)
class GatewayResult:
    run_id: str
    state_hash: str
    receipt_hashes: list[str]
    replay_ok: bool


def _repo_root() -> Path:
    path = Path(__file__).resolve()
    for _ in range(4):
        path = path.parent
    return path


def _backend_src() -> Path:
    return _repo_root() / "apps" / "nyx-backend" / "src"


def _run_root() -> Path:
    root = _repo_root() / "apps" / "nyx-backend-gateway" / "runs"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _db_path() -> Path:
    data_dir = _repo_root() / "apps" / "nyx-backend-gateway" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "nyx_gateway.db"


def _deterministic_id(prefix: str, run_id: str) -> str:
    digest = hashlib.sha256(f"{prefix}:{run_id}".encode("utf-8")).hexdigest()
    return f"{prefix}-{digest[:16]}"


def _require_text(payload: dict[str, Any], key: str, max_len: int = 64) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value or isinstance(value, bool):
        raise GatewayError(f"{key} required")
    if len(value) > max_len:
        raise GatewayError(f"{key} too long")
    return value


def _require_int(payload: dict[str, Any], key: str, min_value: int = 1) -> int:
    value = payload.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise GatewayError(f"{key} must be int")
    if value < min_value:
        raise GatewayError(f"{key} out of bounds")
    return value


def _validate_exchange_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "asset_in": _require_text(payload, "asset_in"),
        "asset_out": _require_text(payload, "asset_out"),
        "amount": _require_int(payload, "amount", 1),
        "min_out": _require_int(payload, "min_out", 1),
    }


def _validate_chat_payload(payload: dict[str, Any]) -> dict[str, Any]:
    channel = _require_text(payload, "channel")
    message = _require_text(payload, "message", max_len=280)
    return {"channel": channel, "message": message}


def _validate_market_payload(payload: dict[str, Any]) -> dict[str, Any]:
    sku = _require_text(payload, "sku")
    title = _require_text(payload, "title", max_len=120)
    price = _require_int(payload, "price", 1)
    qty = _require_int(payload, "qty", 1)
    return {"sku": sku, "title": title, "price": price, "qty": qty}


def _validate_entertainment_payload(payload: dict[str, Any]) -> dict[str, Any]:
    mode = _require_text(payload, "mode", max_len=32)
    step = _require_int(payload, "step", 0)
    return {"mode": mode, "step": step}


def execute_run(
    *,
    seed: int,
    run_id: str,
    module: str,
    action: str,
    payload: dict[str, Any] | None,
    db_path: Path | None = None,
    run_root: Path | None = None,
) -> GatewayResult:
    if payload is None:
        payload = {}
    if module == "exchange" and action == "route_swap":
        payload = _validate_exchange_payload(payload)
    elif module == "chat" and action == "message_event":
        payload = _validate_chat_payload(payload)
    elif module == "marketplace" and action == "order_intent":
        payload = _validate_market_payload(payload)
    elif module == "entertainment" and action == "state_step":
        payload = _validate_entertainment_payload(payload)

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
            receipt_id=_deterministic_id("receipt", run_id),
            module=module,
            action=action,
            state_hash=evidence.state_hash,
            receipt_hashes=evidence.receipt_hashes,
            replay_ok=evidence.replay_ok,
            run_id=run_id,
        ),
    )
    if module == "exchange" and action == "route_swap":
        insert_order(
            conn,
            Order(
                order_id=_deterministic_id("order", run_id),
                side="BUY",
                amount=payload["amount"],
                price=payload["min_out"],
                asset_in=payload["asset_in"],
                asset_out=payload["asset_out"],
                run_id=run_id,
            ),
        )
        insert_trade(
            conn,
            Trade(
                trade_id=_deterministic_id("trade", run_id),
                order_id=_deterministic_id("order", run_id),
                amount=payload["amount"],
                price=payload["min_out"],
                run_id=run_id,
            ),
        )
    if module == "chat" and action == "message_event":
        insert_message_event(
            conn,
            MessageEvent(
                message_id=_deterministic_id("message", run_id),
                channel=payload["channel"],
                body=payload["message"],
                run_id=run_id,
            ),
        )
    if module == "marketplace" and action == "order_intent":
        insert_listing(
            conn,
            Listing(
                listing_id=_deterministic_id("listing", run_id),
                sku=payload["sku"],
                title=payload["title"],
                price=payload["price"],
                run_id=run_id,
            ),
        )
        insert_purchase(
            conn,
            Purchase(
                purchase_id=_deterministic_id("purchase", run_id),
                listing_id=_deterministic_id("listing", run_id),
                qty=payload["qty"],
                run_id=run_id,
            ),
        )
    conn.close()

    return GatewayResult(
        run_id=run_id,
        state_hash=evidence.state_hash,
        receipt_hashes=evidence.receipt_hashes,
        replay_ok=evidence.replay_ok,
    )
