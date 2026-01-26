from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
from pathlib import Path
from typing import Any

from nyx_backend_gateway.exchange import ExchangeError, cancel_order, place_order
from nyx_backend_gateway.fees import route_fee
from nyx_backend_gateway.storage import (
    EvidenceRun,
    EntertainmentEvent,
    EntertainmentItem,
    FeeLedger,
    Listing,
    MessageEvent,
    Order,
    Purchase,
    Receipt,
    apply_wallet_faucet,
    apply_wallet_faucet_with_fee,
    apply_wallet_transfer,
    create_connection,
    insert_entertainment_event,
    insert_entertainment_item,
    insert_evidence_run,
    insert_fee_ledger,
    insert_listing,
    insert_message_event,
    insert_purchase,
    insert_receipt,
    get_wallet_balance,
    load_by_id,
)


class GatewayError(ValueError):
    pass


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


def _require_address(payload: dict[str, Any], key: str) -> str:
    value = _require_text(payload, key, max_len=64)
    if not _ADDRESS_PATTERN.fullmatch(value):
        raise GatewayError(f"{key} invalid")
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
    return {
        "from_address": from_address,
        "to_address": to_address,
        "amount": amount,
    }


def _validate_wallet_faucet(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise GatewayError("payload must be object")
    address = _require_address(payload, "address")
    amount = _require_amount(payload, "amount", max_value=_MAX_AMOUNT)
    return {
        "address": address,
        "amount": amount,
    }


def _require_token(payload: dict[str, Any], key: str = "token") -> str:
    token = payload.get(key, "NYXT")
    if not isinstance(token, str) or not token or isinstance(token, bool):
        raise GatewayError("token invalid")
    if token != "NYXT":
        raise GatewayError("token unsupported")
    return token


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
    return {
        "side": side,
        "asset_in": _require_text(payload, "asset_in"),
        "asset_out": _require_text(payload, "asset_out"),
        "amount": _require_int(payload, "amount", 1, _MAX_AMOUNT),
        "price": _require_int(payload, "price", 1, _MAX_PRICE),
    }


def _validate_cancel(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "order_id": _require_text(payload, "order_id"),
    }


def _validate_chat_payload(payload: dict[str, Any]) -> dict[str, Any]:
    channel = _require_text(payload, "channel")
    message = _require_text(payload, "message", max_len=280)
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
    return {"sku": sku, "title": title, "price": price}


def _validate_purchase_payload(payload: dict[str, Any]) -> dict[str, Any]:
    listing_id = _require_text(payload, "listing_id")
    qty = _require_int(payload, "qty", 1, _MAX_AMOUNT)
    return {"listing_id": listing_id, "qty": qty}


def _validate_entertainment_payload(payload: dict[str, Any]) -> dict[str, Any]:
    item_id = _require_text(payload, "item_id", max_len=32)
    mode = _require_text(payload, "mode", max_len=32)
    if mode not in _ENTERTAINMENT_MODES:
        raise GatewayError("mode not allowed")
    step = _require_int(payload, "step", 0, 20)
    return {"item_id": item_id, "mode": mode, "step": step}


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
    if module == "exchange" and action in {"route_swap"}:
        payload = _validate_exchange_payload(payload)
    if module == "exchange" and action == "place_order":
        payload = _validate_place_order(payload)
    if module == "exchange" and action == "cancel_order":
        payload = _validate_cancel(payload)
    if module == "chat" and action == "message_event":
        payload = _validate_chat_payload(payload)
    if module == "marketplace" and action == "order_intent":
        payload = _validate_market_payload(payload)
    if module == "marketplace" and action == "listing_publish":
        payload = _validate_listing_payload(payload)
    if module == "marketplace" and action == "purchase_listing":
        payload = _validate_purchase_payload(payload)
    if module == "entertainment" and action == "state_step":
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
    if module == "marketplace" and action in {"order_intent", "listing_publish", "purchase_listing"}:
        fee_record = route_fee(module, action, payload, run_id)
        insert_fee_ledger(conn, fee_record)

    if module == "exchange" and action == "place_order":
        order = Order(
            order_id=_order_id(run_id),
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
            cancel_order(conn, payload["order_id"])
        except ExchangeError as exc:
            raise GatewayError(str(exc)) from exc

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
    if module == "marketplace" and action == "listing_publish":
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
    if module == "marketplace" and action == "purchase_listing":
        listing_record = load_by_id(conn, "listings", "listing_id", payload["listing_id"])
        if listing_record is None:
            raise GatewayError("listing_id not found")
        insert_purchase(
            conn,
            Purchase(
                purchase_id=_deterministic_id("purchase", run_id),
                listing_id=payload["listing_id"],
                qty=payload["qty"],
                run_id=run_id,
            ),
        )
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
    fee_record = route_fee("wallet", "transfer", validated, run_id)
    conn = create_connection(db_path or _db_path())
    from_balance = get_wallet_balance(conn, validated["from_address"])
    total_debit = validated["amount"] + fee_record.total_paid
    if from_balance < total_debit:
        raise GatewayError("insufficient balance")

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
) -> tuple[GatewayResult, int]:
    validated = _validate_wallet_faucet(payload)
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
    balance = apply_wallet_faucet(
        conn,
        validated["address"],
        validated["amount"],
    )
    return (
        GatewayResult(
            run_id=run_id,
            state_hash=evidence.state_hash,
            receipt_hashes=evidence.receipt_hashes,
            replay_ok=evidence.replay_ok,
        ),
        balance,
    )


def execute_wallet_faucet_v1(
    *,
    seed: int,
    run_id: str,
    payload: dict[str, Any],
    account_id: str,
    db_path: Path | None = None,
    run_root: Path | None = None,
) -> tuple[GatewayResult, int, FeeLedger]:
    validated = _validate_wallet_faucet(payload)
    _require_token(payload)
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
    fee_record = route_fee("wallet", "faucet_v1", {"amount": validated["amount"]}, run_id)
    if fee_record.total_paid <= 0:
        raise GatewayError("fee_total must be nonzero")
    balances = apply_wallet_faucet_with_fee(
        conn,
        address=validated["address"],
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
        balances["balance"],
        fee_record,
    )


def fetch_wallet_balance(*, address: str, db_path: Path | None = None) -> int:
    conn = create_connection(db_path or _db_path())
    return get_wallet_balance(conn, address)
