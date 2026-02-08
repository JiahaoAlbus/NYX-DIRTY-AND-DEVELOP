from __future__ import annotations

import re
import time
from typing import Any

from nyx_backend_gateway.errors import GatewayApiError, GatewayError
from nyx_backend_gateway.evidence_adapter import run_and_record
from nyx_backend_gateway.fees import route_fee
from nyx_backend_gateway.identifiers import deterministic_id
from nyx_backend_gateway.models import GatewayResult
from nyx_backend_gateway.paths import db_path as default_db_path, run_root as default_run_root
from nyx_backend_gateway.storage import (
    AirdropClaim,
    FeeLedger,
    apply_wallet_faucet_with_fee,
    create_connection,
    insert_airdrop_claim,
    insert_fee_ledger,
    insert_faucet_claim,
)
from nyx_backend_gateway.validation import validate_address_text


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
    acct = validate_address_text(account_id, "account_id")

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
    db_path=None,
    run_root=None,
) -> tuple[GatewayResult, int, FeeLedger, dict[str, object]]:
    acct = validate_address_text(account_id, "account_id")
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

    conn = create_connection(db_path or default_db_path())
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
            raise GatewayApiError("TASK_INCOMPLETE", "task not completed", http_status=409, details={"task_id": task_id})

        fee_record = route_fee("wallet", "airdrop", {"amount": reward}, run_id)
        outcome = run_and_record(
            seed=seed,
            run_id=run_id,
            module="wallet",
            action="airdrop",
            payload={"task_id": task_id, "reward": reward, "account_id": acct},
            conn=conn,
            base_dir=run_root or default_run_root(),
        )

        faucet_result = apply_wallet_faucet_with_fee(
            conn,
            address=acct,
            amount=reward,
            fee_total=fee_record.total_paid,
            treasury_address=fee_record.fee_address,
            run_id=f"airdrop-{task_id}-{run_id}",
            asset_id="NYXT",
        )
        insert_fee_ledger(conn, fee_record)
        insert_airdrop_claim(
            conn,
            AirdropClaim(
                claim_id=deterministic_id("airdrop-claim", run_id),
                account_id=acct,
                task_id=task_id,
                reward=reward,
                created_at=int(time.time()),
                run_id=run_id,
            ),
        )
        conn.commit()
        return (
            GatewayResult(run_id=run_id, state_hash=outcome.state_hash, receipt_hashes=outcome.receipt_hashes, replay_ok=outcome.replay_ok),
            int(faucet_result["balance"]),
            fee_record,
            {"task_id": task_id, "reward": reward, "completion_run_id": completion_run_id},
        )
    finally:
        conn.close()


def execute_airdrop_claim(
    *,
    seed: int,
    run_id: str,
    payload: dict[str, Any],
    db_path=None,
    run_root=None,
) -> tuple[GatewayResult, dict[str, int], FeeLedger]:
    if not isinstance(payload, dict):
        raise GatewayError("payload must be object")
    address = validate_address_text(payload.get("address"), "address")
    task_id = payload.get("task_id")
    if not isinstance(task_id, str) or not task_id or isinstance(task_id, bool):
        raise GatewayError("task_id required")
    reward = payload.get("reward")
    if not isinstance(reward, int) or isinstance(reward, bool) or reward <= 0:
        raise GatewayError("reward invalid")
    amount = int(reward)

    fee_record = route_fee("wallet", "airdrop", payload, run_id)
    conn = create_connection(db_path or default_db_path())

    existing = conn.execute(
        "SELECT 1 FROM wallet_transfers WHERE to_address = ? AND run_id LIKE ?",
        (address, f"airdrop-{task_id}-%"),
    ).fetchone()
    if existing:
        raise GatewayError("Airdrop already claimed for this task")

    outcome = run_and_record(
        seed=seed,
        run_id=run_id,
        module="wallet",
        action="airdrop",
        payload=payload,
        conn=conn,
        base_dir=run_root or default_run_root(),
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
        GatewayResult(run_id=run_id, state_hash=outcome.state_hash, receipt_hashes=outcome.receipt_hashes, replay_ok=outcome.replay_ok),
        result,
        fee_record,
    )
