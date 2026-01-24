from __future__ import annotations

from dataclasses import dataclass
import json
import re
import sqlite3
from pathlib import Path

from nyx_backend_gateway.migrations import apply_migrations


class StorageError(ValueError):
    pass


def create_connection(db_path: Path) -> sqlite3.Connection:
    if not isinstance(db_path, Path):
        raise StorageError("db_path must be Path")
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    apply_migrations(conn)
    return conn


def _validate_text(value: object, name: str, pattern: str = r"[A-Za-z0-9_./-]{1,128}") -> str:
    if not isinstance(value, str) or not value or isinstance(value, bool):
        raise StorageError(f"{name} required")
    if not re.fullmatch(pattern, value):
        raise StorageError(f"{name} invalid")
    return value


def _validate_int(value: object, name: str, min_value: int = 0) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise StorageError(f"{name} must be int")
    if value < min_value:
        raise StorageError(f"{name} out of bounds")
    return value


@dataclass(frozen=True)
class EvidenceRun:
    run_id: str
    module: str
    action: str
    seed: int
    state_hash: str
    receipt_hashes: list[str]
    replay_ok: bool


@dataclass(frozen=True)
class Order:
    order_id: str
    side: str
    amount: int
    price: int
    asset_in: str
    asset_out: str
    run_id: str


@dataclass(frozen=True)
class Trade:
    trade_id: str
    order_id: str
    amount: int
    price: int
    run_id: str


@dataclass(frozen=True)
class MessageEvent:
    message_id: str
    channel: str
    body: str
    run_id: str


@dataclass(frozen=True)
class Listing:
    listing_id: str
    sku: str
    title: str
    price: int
    run_id: str


@dataclass(frozen=True)
class Purchase:
    purchase_id: str
    listing_id: str
    qty: int
    run_id: str


@dataclass(frozen=True)
class EntertainmentItem:
    item_id: str
    title: str
    summary: str
    category: str


@dataclass(frozen=True)
class EntertainmentEvent:
    event_id: str
    item_id: str
    mode: str
    step: int
    run_id: str


@dataclass(frozen=True)
class Receipt:
    receipt_id: str
    module: str
    action: str
    state_hash: str
    receipt_hashes: list[str]
    replay_ok: bool
    run_id: str


@dataclass(frozen=True)
class FeeLedger:
    fee_id: str
    module: str
    action: str
    protocol_fee_total: int
    platform_fee_amount: int
    total_paid: int
    fee_address: str
    run_id: str


def insert_evidence_run(conn: sqlite3.Connection, record: EvidenceRun) -> None:
    run_id = _validate_text(record.run_id, "run_id")
    module = _validate_text(record.module, "module")
    action = _validate_text(record.action, "action")
    seed = _validate_int(record.seed, "seed", 0)
    state_hash = _validate_text(record.state_hash, "state_hash", r"[A-Fa-f0-9]{16,128}")
    if not isinstance(record.receipt_hashes, list) or not record.receipt_hashes:
        raise StorageError("receipt_hashes required")
    receipt_hashes = json.dumps(record.receipt_hashes, sort_keys=True, separators=(",", ":"))
    replay_ok = 1 if record.replay_ok else 0
    conn.execute(
        "INSERT INTO evidence_runs (run_id, module, action, seed, state_hash, receipt_hashes, replay_ok) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (run_id, module, action, seed, state_hash, receipt_hashes, replay_ok),
    )
    conn.commit()


def insert_order(conn: sqlite3.Connection, order: Order) -> None:
    order_id = _validate_text(order.order_id, "order_id")
    side = _validate_text(order.side, "side", r"(BUY|SELL)")
    amount = _validate_int(order.amount, "amount", 1)
    price = _validate_int(order.price, "price", 1)
    asset_in = _validate_text(order.asset_in, "asset_in")
    asset_out = _validate_text(order.asset_out, "asset_out")
    run_id = _validate_text(order.run_id, "run_id")
    conn.execute(
        "INSERT INTO orders (order_id, side, amount, price, asset_in, asset_out, run_id) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (order_id, side, amount, price, asset_in, asset_out, run_id),
    )
    conn.commit()


def update_order_amount(conn: sqlite3.Connection, order_id: str, new_amount: int) -> None:
    oid = _validate_text(order_id, "order_id")
    amount = _validate_int(new_amount, "amount", 1)
    conn.execute("UPDATE orders SET amount = ? WHERE order_id = ?", (amount, oid))
    conn.commit()


def delete_order(conn: sqlite3.Connection, order_id: str) -> None:
    oid = _validate_text(order_id, "order_id")
    conn.execute("DELETE FROM orders WHERE order_id = ?", (oid,))
    conn.commit()


def list_orders(
    conn: sqlite3.Connection,
    side: str | None = None,
    asset_in: str | None = None,
    asset_out: str | None = None,
    order_by: str = "price ASC, order_id ASC",
) -> list[dict[str, object]]:
    clauses = []
    params: list[object] = []
    if side:
        clauses.append("side = ?")
        params.append(_validate_text(side, "side", r"(BUY|SELL)"))
    if asset_in:
        clauses.append("asset_in = ?")
        params.append(_validate_text(asset_in, "asset_in"))
    if asset_out:
        clauses.append("asset_out = ?")
        params.append(_validate_text(asset_out, "asset_out"))
    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    if order_by not in {"price ASC, order_id ASC", "price DESC, order_id ASC"}:
        raise StorageError("order_by not allowed")
    rows = conn.execute(
        f"SELECT * FROM orders {where} ORDER BY {order_by}",
        params,
    ).fetchall()
    return [{col: row[col] for col in row.keys()} for row in rows]


def insert_trade(conn: sqlite3.Connection, trade: Trade) -> None:
    trade_id = _validate_text(trade.trade_id, "trade_id")
    order_id = _validate_text(trade.order_id, "order_id")
    amount = _validate_int(trade.amount, "amount", 1)
    price = _validate_int(trade.price, "price", 1)
    run_id = _validate_text(trade.run_id, "run_id")
    conn.execute(
        "INSERT INTO trades (trade_id, order_id, amount, price, run_id) "
        "VALUES (?, ?, ?, ?, ?)",
        (trade_id, order_id, amount, price, run_id),
    )
    conn.commit()


def list_trades(conn: sqlite3.Connection) -> list[dict[str, object]]:
    rows = conn.execute("SELECT * FROM trades ORDER BY trade_id ASC").fetchall()
    return [{col: row[col] for col in row.keys()} for row in rows]


def insert_message_event(conn: sqlite3.Connection, message: MessageEvent) -> None:
    message_id = _validate_text(message.message_id, "message_id")
    channel = _validate_text(message.channel, "channel")
    if not isinstance(message.body, str) or not message.body or isinstance(message.body, bool):
        raise StorageError("body required")
    if len(message.body) > 512:
        raise StorageError("body too long")
    run_id = _validate_text(message.run_id, "run_id")
    conn.execute(
        "INSERT INTO messages (message_id, channel, body, run_id) VALUES (?, ?, ?, ?)",
        (message_id, channel, message.body, run_id),
    )
    conn.commit()


def list_messages(conn: sqlite3.Connection, channel: str | None = None, limit: int = 50) -> list[dict[str, object]]:
    if limit < 1 or limit > 200:
        raise StorageError("limit out of bounds")
    clauses = []
    params: list[object] = []
    if channel:
        clauses.append("channel = ?")
        params.append(_validate_text(channel, "channel"))
    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    rows = conn.execute(
        f"SELECT * FROM messages {where} ORDER BY message_id ASC LIMIT ?",
        (*params, limit),
    ).fetchall()
    return [{col: row[col] for col in row.keys()} for row in rows]


def insert_listing(conn: sqlite3.Connection, listing: Listing) -> None:
    listing_id = _validate_text(listing.listing_id, "listing_id")
    sku = _validate_text(listing.sku, "sku")
    if not isinstance(listing.title, str) or not listing.title or isinstance(listing.title, bool):
        raise StorageError("title required")
    if len(listing.title) > 128:
        raise StorageError("title too long")
    price = _validate_int(listing.price, "price", 1)
    run_id = _validate_text(listing.run_id, "run_id")
    conn.execute(
        "INSERT INTO listings (listing_id, sku, title, price, run_id) VALUES (?, ?, ?, ?, ?)",
        (listing_id, sku, listing.title, price, run_id),
    )
    conn.commit()


def list_listings(conn: sqlite3.Connection, limit: int = 100) -> list[dict[str, object]]:
    if limit < 1 or limit > 500:
        raise StorageError("limit out of bounds")
    rows = conn.execute(
        "SELECT * FROM listings ORDER BY listing_id ASC LIMIT ?",
        (limit,),
    ).fetchall()
    return [{col: row[col] for col in row.keys()} for row in rows]


def insert_purchase(conn: sqlite3.Connection, purchase: Purchase) -> None:
    purchase_id = _validate_text(purchase.purchase_id, "purchase_id")
    listing_id = _validate_text(purchase.listing_id, "listing_id")
    qty = _validate_int(purchase.qty, "qty", 1)
    run_id = _validate_text(purchase.run_id, "run_id")
    conn.execute(
        "INSERT INTO purchases (purchase_id, listing_id, qty, run_id) VALUES (?, ?, ?, ?)",
        (purchase_id, listing_id, qty, run_id),
    )
    conn.commit()


def list_purchases(conn: sqlite3.Connection, listing_id: str | None = None, limit: int = 100) -> list[dict[str, object]]:
    if limit < 1 or limit > 500:
        raise StorageError("limit out of bounds")
    clauses = []
    params: list[object] = []
    if listing_id:
        clauses.append("listing_id = ?")
        params.append(_validate_text(listing_id, "listing_id"))
    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    rows = conn.execute(
        f"SELECT * FROM purchases {where} ORDER BY purchase_id ASC LIMIT ?",
        (*params, limit),
    ).fetchall()
    return [{col: row[col] for col in row.keys()} for row in rows]


def insert_entertainment_item(conn: sqlite3.Connection, item: EntertainmentItem) -> None:
    item_id = _validate_text(item.item_id, "item_id")
    if not isinstance(item.title, str) or not item.title or isinstance(item.title, bool):
        raise StorageError("title required")
    if len(item.title) > 128:
        raise StorageError("title too long")
    if not isinstance(item.summary, str) or not item.summary or isinstance(item.summary, bool):
        raise StorageError("summary required")
    if len(item.summary) > 256:
        raise StorageError("summary too long")
    category = _validate_text(item.category, "category", r"[A-Za-z0-9_-]{1,32}")
    conn.execute(
        "INSERT OR IGNORE INTO entertainment_items (item_id, title, summary, category) VALUES (?, ?, ?, ?)",
        (item_id, item.title, item.summary, category),
    )
    conn.commit()


def list_entertainment_items(conn: sqlite3.Connection, limit: int = 100) -> list[dict[str, object]]:
    if limit < 1 or limit > 200:
        raise StorageError("limit out of bounds")
    rows = conn.execute(
        "SELECT * FROM entertainment_items ORDER BY item_id ASC LIMIT ?",
        (limit,),
    ).fetchall()
    return [{col: row[col] for col in row.keys()} for row in rows]


def insert_entertainment_event(conn: sqlite3.Connection, event: EntertainmentEvent) -> None:
    event_id = _validate_text(event.event_id, "event_id")
    item_id = _validate_text(event.item_id, "item_id")
    mode = _validate_text(event.mode, "mode", r"[A-Za-z0-9_-]{1,32}")
    step = _validate_int(event.step, "step", 0)
    run_id = _validate_text(event.run_id, "run_id")
    conn.execute(
        "INSERT INTO entertainment_events (event_id, item_id, mode, step, run_id) VALUES (?, ?, ?, ?, ?)",
        (event_id, item_id, mode, step, run_id),
    )
    conn.commit()


def list_entertainment_events(
    conn: sqlite3.Connection,
    item_id: str | None = None,
    limit: int = 100,
) -> list[dict[str, object]]:
    if limit < 1 or limit > 200:
        raise StorageError("limit out of bounds")
    clauses = []
    params: list[object] = []
    if item_id:
        clauses.append("item_id = ?")
        params.append(_validate_text(item_id, "item_id"))
    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    rows = conn.execute(
        f"SELECT * FROM entertainment_events {where} ORDER BY event_id ASC LIMIT ?",
        (*params, limit),
    ).fetchall()
    return [{col: row[col] for col in row.keys()} for row in rows]


def insert_receipt(conn: sqlite3.Connection, receipt: Receipt) -> None:
    receipt_id = _validate_text(receipt.receipt_id, "receipt_id")
    module = _validate_text(receipt.module, "module")
    action = _validate_text(receipt.action, "action")
    state_hash = _validate_text(receipt.state_hash, "state_hash", r"[A-Fa-f0-9]{16,128}")
    if not isinstance(receipt.receipt_hashes, list) or not receipt.receipt_hashes:
        raise StorageError("receipt_hashes required")
    receipt_hashes = json.dumps(receipt.receipt_hashes, sort_keys=True, separators=(",", ":"))
    replay_ok = 1 if receipt.replay_ok else 0
    run_id = _validate_text(receipt.run_id, "run_id")
    conn.execute(
        "INSERT INTO receipts (receipt_id, module, action, state_hash, receipt_hashes, replay_ok, run_id) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (receipt_id, module, action, state_hash, receipt_hashes, replay_ok, run_id),
    )
    conn.commit()


def insert_fee_ledger(conn: sqlite3.Connection, record: FeeLedger) -> None:
    fee_id = _validate_text(record.fee_id, "fee_id")
    module = _validate_text(record.module, "module")
    action = _validate_text(record.action, "action")
    protocol_fee_total = _validate_int(record.protocol_fee_total, "protocol_fee_total", 1)
    platform_fee_amount = _validate_int(record.platform_fee_amount, "platform_fee_amount", 0)
    total_paid = _validate_int(record.total_paid, "total_paid", 1)
    fee_address = _validate_text(record.fee_address, "fee_address", r"[A-Za-z0-9_:-]{8,128}")
    run_id = _validate_text(record.run_id, "run_id")
    conn.execute(
        "INSERT INTO fee_ledger (fee_id, module, action, protocol_fee_total, platform_fee_amount, total_paid, fee_address, run_id) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (fee_id, module, action, protocol_fee_total, platform_fee_amount, total_paid, fee_address, run_id),
    )
    conn.commit()


def load_by_id(conn: sqlite3.Connection, table: str, key: str, value: str) -> dict[str, object] | None:
    if table not in {
        "evidence_runs",
        "orders",
        "trades",
        "messages",
        "listings",
        "purchases",
        "entertainment_items",
        "entertainment_events",
        "receipts",
        "fee_ledger",
    }:
        raise StorageError("table not allowed")
    key_name = _validate_text(key, "key", r"[A-Za-z0-9_]{1,32}")
    value_text = _validate_text(value, "value")
    row = conn.execute(
        f"SELECT * FROM {table} WHERE {key_name} = ?",
        (value_text,),
    ).fetchone()
    if row is None:
        return None
    return {col: row[col] for col in row.keys()}
