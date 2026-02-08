from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

from nyx_backend_gateway.airdrop import (
    execute_airdrop_claim as airdrop_execute_airdrop_claim,
)
from nyx_backend_gateway.airdrop import (
    execute_airdrop_claim_v1 as airdrop_execute_airdrop_claim_v1,
)
from nyx_backend_gateway.airdrop import (
    list_airdrop_tasks_v1 as airdrop_list_tasks_v1,
)
from nyx_backend_gateway.assets import supported_assets as assets_supported_assets
from nyx_backend_gateway.chat import record_message_event as chat_record_message_event
from nyx_backend_gateway.env import (
    get_faucet_cooldown_seconds,
    get_faucet_ip_max_claims_per_24h,
    get_faucet_max_amount_per_24h,
    get_faucet_max_claims_per_24h,
)
from nyx_backend_gateway.errors import GatewayApiError, GatewayError
from nyx_backend_gateway.evidence_adapter import run_and_record
from nyx_backend_gateway.exchange import ExchangeError, cancel_order, place_order
from nyx_backend_gateway.fees import route_fee
from nyx_backend_gateway.identifiers import deterministic_id, order_id
from nyx_backend_gateway.marketplace import (
    list_active_listings as marketplace_list_active,
)
from nyx_backend_gateway.marketplace import (
    publish_listing as marketplace_publish_listing,
)
from nyx_backend_gateway.marketplace import (
    purchase_listing as marketplace_purchase_listing,
)
from nyx_backend_gateway.marketplace import (
    search_listings as marketplace_search,
)
from nyx_backend_gateway.models import GatewayResult
from nyx_backend_gateway.storage import (
    EntertainmentEvent,
    EntertainmentItem,
    FaucetClaim,
    FeeLedger,
    Order,
    apply_wallet_faucet_with_fee,
    apply_wallet_transfer,
    create_connection,
    get_wallet_balance,
    insert_entertainment_event,
    insert_entertainment_item,
    insert_faucet_claim,
    insert_fee_ledger,
    load_by_id,
)
from nyx_backend_gateway.validation import (
    validate_cancel,
    validate_chat_payload,
    validate_entertainment_payload,
    validate_listing_payload,
    validate_place_order,
    validate_purchase_payload,
    validate_wallet_faucet,
    validate_wallet_transfer,
)
from nyx_backend_gateway.web2_guard import (
    execute_web2_guard_request as web2_execute_request,
)
from nyx_backend_gateway.web2_guard import (
    fetch_web2_guard_requests as web2_fetch_requests,
)
from nyx_backend_gateway.web2_guard import (
    list_web2_allowlist as web2_list_allowlist,
)


def list_airdrop_tasks_v1(conn, account_id: str) -> list[dict[str, object]]:
    return airdrop_list_tasks_v1(conn, account_id)


def execute_airdrop_claim_v1(
    *,
    seed: int,
    run_id: str,
    account_id: str,
    payload: dict[str, Any],
    db_path: Path | None = None,
    run_root: Path | None = None,
) -> tuple[GatewayResult, int, FeeLedger, dict[str, object]]:
    return airdrop_execute_airdrop_claim_v1(
        seed=seed,
        run_id=run_id,
        account_id=account_id,
        payload=payload,
        db_path=db_path or _db_path(),
        run_root=run_root or _run_root(),
    )


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


def list_web2_allowlist() -> list[dict[str, object]]:
    return web2_list_allowlist()


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
        payload = validate_place_order(payload)
        if caller_account_id and payload.get("owner_address") != caller_account_id:
            raise GatewayError("owner_address mismatch")
    if module == "exchange" and action == "cancel_order":
        payload = validate_cancel(payload)
        # TODO: Verify order ownership in DB
    if module == "chat" and action == "message_event":
        payload = validate_chat_payload(payload)
    if module == "marketplace" and action == "purchase_listing":
        if not caller_account_id:
            raise GatewayError("auth required")
        payload = validate_purchase_payload(payload)
        if caller_account_id and payload.get("buyer_id") != caller_account_id:
            raise GatewayError("buyer_id mismatch")
    if module == "marketplace" and action == "listing_publish":
        if not caller_account_id:
            raise GatewayError("auth required")
        payload = validate_listing_payload(payload)
        if caller_account_id and payload.get("publisher_id") != caller_account_id:
            raise GatewayError("publisher_id mismatch")
    if module == "entertainment" and action == "state_step":
        payload = validate_entertainment_payload(payload)

    conn = create_connection(db_path or _db_path())
    run_root = run_root or _run_root()
    try:
        outcome = run_and_record(
            seed=seed,
            run_id=run_id,
            module=module,
            action=action,
            payload=payload,
            conn=conn,
            base_dir=run_root,
        )

        fee_record: FeeLedger | None = None
        if module == "exchange" and action in {"route_swap", "place_order", "cancel_order"}:
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
                order_id=order_id(run_id),
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
                transfer_id=deterministic_id("fee", run_id),
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
                    transfer_id=deterministic_id("fee", run_id),
                    from_address=caller_account_id,
                    to_address=fee_record.fee_address,
                    asset_id="NYXT",
                    amount=0,
                    fee_total=fee_record.total_paid,
                    treasury_address=fee_record.fee_address,
                    run_id=run_id,
                )
                insert_fee_ledger(conn, fee_record)
            chat_record_message_event(conn, run_id, payload, caller_account_id)
        if module == "marketplace" and action == "listing_publish":
            marketplace_publish_listing(conn, run_id, payload, caller_account_id)
        if module == "marketplace" and action == "purchase_listing":
            marketplace_purchase_listing(conn, run_id, payload, caller_account_id)
        if module == "entertainment" and action == "state_step":
            _ensure_entertainment_items(conn)
            item_record = load_by_id(conn, "entertainment_items", "item_id", payload["item_id"])
            if item_record is None:
                raise GatewayError("item_id not found")
            insert_entertainment_event(
                conn,
                EntertainmentEvent(
                    event_id=deterministic_id("ent-event", run_id),
                    item_id=payload["item_id"],
                    mode=payload["mode"],
                    step=payload["step"],
                    run_id=run_id,
                ),
            )
        if module == "dapp" and action == "sign_request":
            conn.execute(
                "INSERT INTO message_events (message_id, channel, body, run_id) VALUES (?, ?, ?, ?)",
                (deterministic_id("dapp-sig", run_id), payload["dapp_url"], f"Signed: {payload['method']}", run_id),
            )

        return GatewayResult(
            run_id=run_id,
            state_hash=outcome.state_hash,
            receipt_hashes=outcome.receipt_hashes,
            replay_ok=outcome.replay_ok,
        )
    finally:
        conn.close()


def execute_wallet_transfer(
    *,
    seed: int,
    run_id: str,
    payload: dict[str, Any],
    db_path: Path | None = None,
    run_root: Path | None = None,
) -> tuple[GatewayResult, dict[str, int], FeeLedger]:
    validated = validate_wallet_transfer(payload)
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

    outcome = run_and_record(
        seed=seed,
        run_id=run_id,
        module="wallet",
        action="transfer",
        payload=validated,
        conn=conn,
        base_dir=run_root or _run_root(),
    )
    balances = apply_wallet_transfer(
        conn,
        transfer_id=deterministic_id("wallet", run_id),
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
            state_hash=outcome.state_hash,
            receipt_hashes=outcome.receipt_hashes,
            replay_ok=outcome.replay_ok,
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
    validated = validate_wallet_faucet(payload)
    address = validated["address"]
    amount = int(validated.get("amount", 1000))
    asset_id = validated.get("asset_id", "NYXT")

    fee_record = route_fee("wallet", "faucet", validated, run_id)
    conn = create_connection(db_path or _db_path())
    outcome = run_and_record(
        seed=seed,
        run_id=run_id,
        module="wallet",
        action="faucet",
        payload=validated,
        conn=conn,
        base_dir=run_root or _run_root(),
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
            state_hash=outcome.state_hash,
            receipt_hashes=outcome.receipt_hashes,
            replay_ok=outcome.replay_ok,
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
    validated = validate_wallet_faucet(payload)
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
        outcome = run_and_record(
            seed=seed,
            run_id=run_id,
            module="wallet",
            action="faucet",
            payload=validated,
            conn=conn,
            base_dir=run_root or _run_root(),
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
                claim_id=deterministic_id("faucet-claim", run_id),
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
                state_hash=outcome.state_hash,
                receipt_hashes=outcome.receipt_hashes,
                replay_ok=outcome.replay_ok,
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
    return airdrop_execute_airdrop_claim(
        seed=seed,
        run_id=run_id,
        payload=payload,
        db_path=db_path or _db_path(),
        run_root=run_root or _run_root(),
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
    return web2_execute_request(
        seed=seed,
        run_id=run_id,
        payload=payload,
        account_id=account_id,
        db_path=db_path or _db_path(),
        run_root=run_root or _run_root(),
    )


def supported_assets() -> list[dict[str, object]]:
    return assets_supported_assets()


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
    return web2_fetch_requests(
        account_id=account_id,
        limit=limit,
        offset=offset,
        db_path=db_path or _db_path(),
    )


def marketplace_list_active_listings(conn, limit: int = 100, offset: int = 0) -> list[dict[str, object]]:
    return marketplace_list_active(conn, limit=limit, offset=offset)


def marketplace_search_listings(conn, q: str, limit: int = 100, offset: int = 0) -> list[dict[str, object]]:
    return marketplace_search(conn, q=q, limit=limit, offset=offset)
