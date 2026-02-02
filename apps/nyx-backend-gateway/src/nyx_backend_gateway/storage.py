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


def _validate_int(
    value: object,
    name: str,
    min_value: int = 0,
    max_value: int | None = None,
) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise StorageError(f"{name} must be int")
    if value < min_value:
        raise StorageError(f"{name} out of bounds")
    if max_value is not None and value > max_value:
        raise StorageError(f"{name} out of bounds")
    return value


def _validate_wallet_address(value: object, name: str = "address") -> str:
    return _validate_text(value, name, r"[A-Za-z0-9_-]{1,64}")


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
    owner_address: str
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
class PortalAccount:
    account_id: str
    handle: str
    public_key: str
    created_at: int
    status: str
    bio: str | None = None


@dataclass(frozen=True)
class PortalChallenge:
    account_id: str
    nonce: str
    expires_at: int
    used: int


@dataclass(frozen=True)
class PortalSession:
    token: str
    account_id: str
    expires_at: int


@dataclass(frozen=True)
class ChatRoom:
    room_id: str
    name: str
    created_at: int
    is_public: int


@dataclass(frozen=True)
class ChatMessage:
    message_id: str
    room_id: str
    sender_account_id: str
    body: str
    seq: int
    prev_digest: str
    msg_digest: str
    chain_head: str
    created_at: int


@dataclass(frozen=True)
class Listing:
    listing_id: str
    publisher_id: str
    sku: str
    title: str
    price: int
    status: str
    run_id: str


@dataclass(frozen=True)
class Purchase:
    purchase_id: str
    listing_id: str
    buyer_id: str
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


@dataclass(frozen=True)
class WalletAccount:
    address: str
    asset_id: str
    balance: int


@dataclass(frozen=True)
class WalletTransfer:
    transfer_id: str
    from_address: str
    to_address: str
    asset_id: str
    amount: int
    fee_total: int
    treasury_address: str
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
        "INSERT OR REPLACE INTO evidence_runs (run_id, module, action, seed, state_hash, receipt_hashes, replay_ok) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (run_id, module, action, seed, state_hash, receipt_hashes, replay_ok),
    )
    conn.commit()


def insert_portal_account(conn: sqlite3.Connection, account: PortalAccount) -> None:
    account_id = _validate_text(account.account_id, "account_id", r"[A-Za-z0-9_-]{1,64}")
    handle = _validate_text(account.handle, "handle", r"[a-z0-9_-]{3,24}")
    public_key = _validate_text(account.public_key, "public_key", r"[A-Za-z0-9+/=]{16,256}")
    created_at = _validate_int(account.created_at, "created_at", 1)
    status = _validate_text(account.status, "status", r"[A-Za-z0-9_-]{3,16}")
    bio = account.bio
    if bio is not None and len(bio) > 256:
        raise StorageError("bio too long")
    conn.execute(
        "INSERT INTO portal_accounts (account_id, handle, public_key, created_at, status, bio) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (account_id, handle, public_key, created_at, status, bio),
    )
    conn.commit()


def load_portal_account(conn: sqlite3.Connection, account_id: str) -> PortalAccount | None:
    aid = _validate_text(account_id, "account_id", r"[A-Za-z0-9_-]{1,64}")
    row = conn.execute(
        "SELECT account_id, handle, public_key, created_at, status, bio FROM portal_accounts WHERE account_id = ?",
        (aid,),
    ).fetchone()
    if row is None:
        return None
    return PortalAccount(**{col: row[col] for col in row.keys()})


def load_portal_account_by_handle(conn: sqlite3.Connection, handle: str) -> PortalAccount | None:
    h = _validate_text(handle, "handle", r"[a-z0-9_-]{3,24}")
    row = conn.execute(
        "SELECT account_id, handle, public_key, created_at, status, bio FROM portal_accounts WHERE handle = ?",
        (h,),
    ).fetchone()
    if row is None:
        return None
    return PortalAccount(**{col: row[col] for col in row.keys()})


def insert_portal_challenge(conn: sqlite3.Connection, challenge: PortalChallenge) -> None:
    account_id = _validate_text(challenge.account_id, "account_id", r"[A-Za-z0-9_-]{1,64}")
    nonce = _validate_text(challenge.nonce, "nonce", r"[A-Fa-f0-9]{32,128}")
    expires_at = _validate_int(challenge.expires_at, "expires_at", 1)
    used = _validate_int(challenge.used, "used", 0)
    conn.execute(
        "INSERT INTO portal_challenges (account_id, nonce, expires_at, used) "
        "VALUES (?, ?, ?, ?)",
        (account_id, nonce, expires_at, used),
    )
    conn.commit()


def consume_portal_challenge(conn: sqlite3.Connection, account_id: str, nonce: str) -> PortalChallenge | None:
    aid = _validate_text(account_id, "account_id", r"[A-Za-z0-9_-]{1,64}")
    nn = _validate_text(nonce, "nonce", r"[A-Fa-f0-9]{32,128}")
    row = conn.execute(
        "SELECT account_id, nonce, expires_at, used FROM portal_challenges WHERE account_id = ? AND nonce = ?",
        (aid, nn),
    ).fetchone()
    if row is None:
        return None
    challenge = PortalChallenge(**{col: row[col] for col in row.keys()})
    if challenge.used:
        return challenge
    conn.execute(
        "UPDATE portal_challenges SET used = 1 WHERE account_id = ? AND nonce = ?",
        (aid, nn),
    )
    conn.commit()
    return challenge


def insert_portal_session(conn: sqlite3.Connection, session: PortalSession) -> None:
    token = _validate_text(session.token, "token", r"[A-Fa-f0-9]{32,128}")
    account_id = _validate_text(session.account_id, "account_id", r"[A-Za-z0-9_-]{1,64}")
    expires_at = _validate_int(session.expires_at, "expires_at", 1)
    conn.execute(
        "INSERT INTO portal_sessions (token, account_id, expires_at) VALUES (?, ?, ?)",
        (token, account_id, expires_at),
    )
    conn.commit()


def load_portal_session(conn: sqlite3.Connection, token: str) -> PortalSession | None:
    tok = _validate_text(token, "token", r"[A-Fa-f0-9]{32,128}")
    row = conn.execute(
        "SELECT token, account_id, expires_at FROM portal_sessions WHERE token = ?",
        (tok,),
    ).fetchone()
    if row is None:
        return None
    return PortalSession(**{col: row[col] for col in row.keys()})


def delete_portal_session(conn: sqlite3.Connection, token: str) -> None:
    tok = _validate_text(token, "token", r"[A-Fa-f0-9]{32,128}")
    conn.execute("DELETE FROM portal_sessions WHERE token = ?", (tok,))
    conn.commit()


def insert_chat_room(conn: sqlite3.Connection, room: ChatRoom) -> None:
    room_id = _validate_text(room.room_id, "room_id", r"[A-Za-z0-9_-]{1,64}")
    name = _validate_text(room.name, "name", r"[A-Za-z0-9_ -]{3,48}")
    created_at = _validate_int(room.created_at, "created_at", 1)
    is_public = _validate_int(room.is_public, "is_public", 0)
    conn.execute(
        "INSERT OR REPLACE INTO chat_rooms (room_id, name, created_at, is_public) VALUES (?, ?, ?, ?)",
        (room_id, name, created_at, is_public),
    )
    conn.commit()


def list_chat_rooms(conn: sqlite3.Connection) -> list[dict[str, object]]:
    rows = conn.execute(
        "SELECT room_id, name, created_at, is_public FROM chat_rooms ORDER BY created_at ASC, room_id ASC"
    ).fetchall()
    return [{col: row[col] for col in row.keys()} for row in rows]


def insert_chat_message(conn: sqlite3.Connection, message: ChatMessage) -> None:
    message_id = _validate_text(message.message_id, "message_id", r"[A-Za-z0-9_-]{1,64}")
    room_id = _validate_text(message.room_id, "room_id", r"[A-Za-z0-9_-]{1,64}")
    sender = _validate_text(message.sender_account_id, "sender_account_id", r"[A-Za-z0-9_-]{1,64}")
    body = _validate_text(message.body, "body", r"[^\x00-\x08\x0b\x0c\x0e-\x1f]{1,512}")
    seq = _validate_int(message.seq, "seq", 1)
    prev_digest = _validate_text(message.prev_digest, "prev_digest", r"[A-Fa-f0-9]{16,128}")
    msg_digest = _validate_text(message.msg_digest, "msg_digest", r"[A-Fa-f0-9]{16,128}")
    chain_head = _validate_text(message.chain_head, "chain_head", r"[A-Fa-f0-9]{16,128}")
    created_at = _validate_int(message.created_at, "created_at", 1)
    conn.execute(
        "INSERT OR REPLACE INTO chat_messages (message_id, room_id, sender_account_id, body, seq, prev_digest, msg_digest, "
        "chain_head, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (message_id, room_id, sender, body, seq, prev_digest, msg_digest, chain_head, created_at),
    )
    conn.commit()


def list_chat_messages(conn: sqlite3.Connection, room_id: str, after: int | None, limit: int) -> list[dict[str, object]]:
    rid = _validate_text(room_id, "room_id", r"[A-Za-z0-9_-]{1,64}")
    lim = _validate_int(limit, "limit", 1)
    params: list[object] = [rid]
    clause = ""
    if after is not None:
        clause = "AND seq > ?"
        params.append(_validate_int(after, "after", 0))
    params.append(lim)
    rows = conn.execute(
        "SELECT message_id, room_id, sender_account_id, body, seq, prev_digest, msg_digest, chain_head, created_at "
        "FROM chat_messages WHERE room_id = ? "
        f"{clause} ORDER BY seq ASC, message_id ASC LIMIT ?",
        tuple(params),
    ).fetchall()
    return [{col: row[col] for col in row.keys()} for row in rows]


def list_receipts(conn: sqlite3.Connection, limit: int = 50, offset: int = 0) -> list[dict[str, object]]:
    lim = _validate_int(limit, "limit", 1, 500)
    off = _validate_int(offset, "offset", 0)
    rows = conn.execute(
        "SELECT receipt_id, module, action, state_hash, receipt_hashes, replay_ok, run_id "
        "FROM receipts ORDER BY receipt_id ASC LIMIT ? OFFSET ?",
        (lim, off),
    ).fetchall()
    results = []
    for row in rows:
        record = {col: row[col] for col in row.keys()}
        raw_hashes = record.get("receipt_hashes", "[]")
        try:
            record["receipt_hashes"] = json.loads(raw_hashes)
        except json.JSONDecodeError:
            record["receipt_hashes"] = []
        record["replay_ok"] = bool(record.get("replay_ok"))
        results.append(record)
    return results


def insert_order(conn: sqlite3.Connection, order: Order) -> None:
    order_id = _validate_text(order.order_id, "order_id")
    owner_address = _validate_wallet_address(order.owner_address, "owner_address")
    side = _validate_text(order.side, "side", r"(BUY|SELL)")
    amount = _validate_int(order.amount, "amount", 1)
    price = _validate_int(order.price, "price", 1)
    asset_in = _validate_text(order.asset_in, "asset_in")
    asset_out = _validate_text(order.asset_out, "asset_out")
    run_id = _validate_text(order.run_id, "run_id")
    conn.execute(
        "INSERT OR REPLACE INTO orders (order_id, owner_address, side, amount, price, asset_in, asset_out, run_id) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (order_id, owner_address, side, amount, price, asset_in, asset_out, run_id),
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
    limit: int = 100,
    offset: int = 0,
) -> list[dict[str, object]]:
    lim = _validate_int(limit, "limit", 1, 1000)
    off = _validate_int(offset, "offset", 0)
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
        f"SELECT * FROM orders {where} ORDER BY {order_by} LIMIT ? OFFSET ?",
        (*params, lim, off),
    ).fetchall()
    return [{col: row[col] for col in row.keys()} for row in rows]


def insert_trade(conn: sqlite3.Connection, trade: Trade) -> None:
    trade_id = _validate_text(trade.trade_id, "trade_id")
    order_id = _validate_text(trade.order_id, "order_id")
    amount = _validate_int(trade.amount, "amount", 1)
    price = _validate_int(trade.price, "price", 1)
    run_id = _validate_text(trade.run_id, "run_id")
    conn.execute(
        "INSERT OR REPLACE INTO trades (trade_id, order_id, amount, price, run_id) "
        "VALUES (?, ?, ?, ?, ?)",
        (trade_id, order_id, amount, price, run_id),
    )
    conn.commit()


def list_trades(conn: sqlite3.Connection, limit: int = 100, offset: int = 0) -> list[dict[str, object]]:
    lim = _validate_int(limit, "limit", 1, 1000)
    off = _validate_int(offset, "offset", 0)
    rows = conn.execute("SELECT * FROM trades ORDER BY trade_id ASC LIMIT ? OFFSET ?", (lim, off)).fetchall()
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
        "INSERT OR REPLACE INTO messages (message_id, channel, body, run_id) VALUES (?, ?, ?, ?)",
        (message_id, channel, message.body, run_id),
    )
    conn.commit()


def list_messages(conn: sqlite3.Connection, channel: str | None = None, limit: int = 50, offset: int = 0) -> list[dict[str, object]]:
    lim = _validate_int(limit, "limit", 1, 500)
    off = _validate_int(offset, "offset", 0)
    clauses = []
    params: list[object] = []
    if channel:
        clauses.append("channel = ?")
        params.append(_validate_text(channel, "channel"))
    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    rows = conn.execute(
        f"SELECT * FROM messages {where} ORDER BY message_id ASC LIMIT ? OFFSET ?",
        (*params, lim, off),
    ).fetchall()
    return [{col: row[col] for col in row.keys()} for row in rows]


def insert_listing(conn: sqlite3.Connection, listing: Listing) -> None:
    listing_id = _validate_text(listing.listing_id, "listing_id")
    publisher_id = _validate_text(listing.publisher_id, "publisher_id")
    sku = _validate_text(listing.sku, "sku")
    if not isinstance(listing.title, str) or not listing.title or isinstance(listing.title, bool):
        raise StorageError("title required")
    if len(listing.title) > 128:
        raise StorageError("title too long")
    price = _validate_int(listing.price, "price", 1)
    status = _validate_text(listing.status, "status", r"(active|sold)")
    run_id = _validate_text(listing.run_id, "run_id")
    conn.execute(
        "INSERT OR REPLACE INTO listings (listing_id, publisher_id, sku, title, price, status, run_id) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (listing_id, publisher_id, sku, listing.title, price, status, run_id),
    )
    conn.commit()


def list_listings(conn: sqlite3.Connection, limit: int = 100, offset: int = 0) -> list[dict[str, object]]:
    lim = _validate_int(limit, "limit", 1, 1000)
    off = _validate_int(offset, "offset", 0)
    rows = conn.execute(
        "SELECT * FROM listings WHERE status = 'active' ORDER BY listing_id ASC LIMIT ? OFFSET ?",
        (lim, off),
    ).fetchall()
    return [{col: row[col] for col in row.keys()} for row in rows]


def insert_purchase(conn: sqlite3.Connection, purchase: Purchase) -> None:
    purchase_id = _validate_text(purchase.purchase_id, "purchase_id")
    listing_id = _validate_text(purchase.listing_id, "listing_id")
    buyer_id = _validate_text(purchase.buyer_id, "buyer_id")
    qty = _validate_int(purchase.qty, "qty", 1)
    run_id = _validate_text(purchase.run_id, "run_id")
    conn.execute(
        "INSERT OR REPLACE INTO purchases (purchase_id, listing_id, buyer_id, qty, run_id) VALUES (?, ?, ?, ?, ?)",
        (purchase_id, listing_id, buyer_id, qty, run_id),
    )
    conn.commit()


def list_purchases(conn: sqlite3.Connection, listing_id: str | None = None, limit: int = 100, offset: int = 0) -> list[dict[str, object]]:
    lim = _validate_int(limit, "limit", 1, 1000)
    off = _validate_int(offset, "offset", 0)
    clauses = []
    params: list[object] = []
    if listing_id:
        clauses.append("listing_id = ?")
        params.append(_validate_text(listing_id, "listing_id"))
    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    rows = conn.execute(
        f"SELECT * FROM purchases {where} ORDER BY purchase_id ASC LIMIT ? OFFSET ?",
        (*params, lim, off),
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


def list_entertainment_items(conn: sqlite3.Connection, limit: int = 100, offset: int = 0) -> list[dict[str, object]]:
    lim = _validate_int(limit, "limit", 1, 1000)
    off = _validate_int(offset, "offset", 0)
    rows = conn.execute(
        "SELECT * FROM entertainment_items ORDER BY item_id ASC LIMIT ? OFFSET ?",
        (lim, off),
    ).fetchall()
    return [{col: row[col] for col in row.keys()} for row in rows]


def insert_entertainment_event(conn: sqlite3.Connection, event: EntertainmentEvent) -> None:
    event_id = _validate_text(event.event_id, "event_id")
    item_id = _validate_text(event.item_id, "item_id")
    mode = _validate_text(event.mode, "mode", r"[A-Za-z0-9_-]{1,32}")
    step = _validate_int(event.step, "step", 0)
    run_id = _validate_text(event.run_id, "run_id")
    conn.execute(
        "INSERT OR REPLACE INTO entertainment_events (event_id, item_id, mode, step, run_id) VALUES (?, ?, ?, ?, ?)",
        (event_id, item_id, mode, step, run_id),
    )
    conn.commit()


def list_entertainment_events(
    conn: sqlite3.Connection,
    item_id: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict[str, object]]:
    lim = _validate_int(limit, "limit", 1, 1000)
    off = _validate_int(offset, "offset", 0)
    clauses = []
    params: list[object] = []
    if item_id:
        clauses.append("item_id = ?")
        params.append(_validate_text(item_id, "item_id"))
    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    rows = conn.execute(
        f"SELECT * FROM entertainment_events {where} ORDER BY event_id ASC LIMIT ? OFFSET ?",
        (*params, lim, off),
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
        "INSERT OR REPLACE INTO receipts (receipt_id, module, action, state_hash, receipt_hashes, replay_ok, run_id) "
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
        "INSERT OR REPLACE INTO fee_ledger (fee_id, module, action, protocol_fee_total, platform_fee_amount, total_paid, fee_address, run_id) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (fee_id, module, action, protocol_fee_total, platform_fee_amount, total_paid, fee_address, run_id),
    )
    conn.commit()


def _ensure_wallet_account(conn: sqlite3.Connection, address: str, asset_id: str = "NYXT") -> None:
    addr = _validate_wallet_address(address)
    asset = _validate_text(asset_id, "asset_id", r"[A-Z0-9]{3,12}")
    conn.execute(
        "INSERT OR IGNORE INTO wallet_accounts (address, asset_id, balance) VALUES (?, ?, ?)",
        (addr, asset, 0),
    )


def get_wallet_balance(conn: sqlite3.Connection, address: str, asset_id: str = "NYXT") -> int:
    addr = _validate_wallet_address(address)
    asset = _validate_text(asset_id, "asset_id", r"[A-Z0-9]{3,12}")
    _ensure_wallet_account(conn, addr, asset)
    row = conn.execute(
        "SELECT balance FROM wallet_accounts WHERE address = ? AND asset_id = ?",
        (addr, asset),
    ).fetchone()
    if row is None:
        return 0
    return int(row[0])


def set_wallet_balance(conn: sqlite3.Connection, address: str, balance: int, asset_id: str = "NYXT") -> None:
    addr = _validate_wallet_address(address)
    asset = _validate_text(asset_id, "asset_id", r"[A-Z0-9]{3,12}")
    amount = _validate_int(balance, "balance", 0)
    _ensure_wallet_account(conn, addr, asset)
    conn.execute(
        "UPDATE wallet_accounts SET balance = ? WHERE address = ? AND asset_id = ?",
        (amount, addr, asset),
    )


def insert_wallet_transfer(conn: sqlite3.Connection, transfer: WalletTransfer) -> None:
    transfer_id = _validate_text(transfer.transfer_id, "transfer_id")
    from_address = _validate_wallet_address(transfer.from_address, "from_address")
    to_address = _validate_wallet_address(transfer.to_address, "to_address")
    asset_id = _validate_text(transfer.asset_id, "asset_id", r"[A-Z0-9]{3,12}")
    amount = _validate_int(transfer.amount, "amount", 1)
    fee_total = _validate_int(transfer.fee_total, "fee_total", 0)
    treasury_address = _validate_wallet_address(transfer.treasury_address, "treasury_address")
    run_id = _validate_text(transfer.run_id, "run_id")
    conn.execute(
        "INSERT OR REPLACE INTO wallet_transfers (transfer_id, from_address, to_address, asset_id, amount, fee_total, treasury_address, run_id) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (transfer_id, from_address, to_address, asset_id, amount, fee_total, treasury_address, run_id),
    )


def apply_wallet_transfer(
    conn: sqlite3.Connection,
    *,
    transfer_id: str,
    from_address: str,
    to_address: str,
    amount: int,
    fee_total: int,
    treasury_address: str,
    run_id: str,
    asset_id: str = "NYXT",
) -> dict[str, int]:
    transfer_id = _validate_text(transfer_id, "transfer_id")
    from_addr = _validate_wallet_address(from_address, "from_address")
    to_addr = _validate_wallet_address(to_address, "to_address")
    treasury_addr = _validate_wallet_address(treasury_address, "treasury_address")
    asset = _validate_text(asset_id, "asset_id", r"[A-Z0-9]{3,12}")
    amt = _validate_int(amount, "amount", 1)
    fee = _validate_int(fee_total, "fee_total", 0)
    if from_addr == to_addr:
        raise StorageError("from_address must differ")
    _ensure_wallet_account(conn, from_addr, asset)
    _ensure_wallet_account(conn, to_addr, asset)
    _ensure_wallet_account(conn, treasury_addr, "NYXT") # Fees always in NYXT
    
    current = get_wallet_balance(conn, from_addr, asset)
    if current < amt:
        raise StorageError(f"insufficient {asset} balance")
    
    # Handle fee separately if it's in NYXT
    if asset == "NYXT":
        if current < (amt + fee):
            raise StorageError("insufficient balance for amount + fee")
        new_from = current - (amt + fee)
    else:
        nyxt_balance = get_wallet_balance(conn, from_addr, "NYXT")
        if nyxt_balance < fee:
            raise StorageError("insufficient NYXT for fee")
        new_from = current - amt
        set_wallet_balance(conn, from_addr, nyxt_balance - fee, "NYXT")

    new_to = get_wallet_balance(conn, to_addr, asset) + amt
    new_treasury = get_wallet_balance(conn, treasury_addr, "NYXT") + fee
    
    set_wallet_balance(conn, from_addr, new_from, asset)
    set_wallet_balance(conn, to_addr, new_to, asset)
    set_wallet_balance(conn, treasury_addr, new_treasury, "NYXT")
    
    insert_wallet_transfer(
        conn,
        WalletTransfer(
            transfer_id=transfer_id,
            from_address=from_addr,
            to_address=to_addr,
            asset_id=asset,
            amount=amt,
            fee_total=fee,
            treasury_address=treasury_addr,
            run_id=run_id,
        ),
    )
    conn.commit()
    return {
        "from_balance": new_from,
        "to_balance": new_to,
        "treasury_balance": new_treasury,
    }


def apply_wallet_faucet(conn: sqlite3.Connection, address: str, amount: int, asset_id: str = "NYXT") -> int:
    addr = _validate_wallet_address(address)
    amt = _validate_int(amount, "amount", 1)
    asset = _validate_text(asset_id, "asset_id", r"[A-Z0-9]{3,12}")
    _ensure_wallet_account(conn, addr, asset)
    current = get_wallet_balance(conn, addr, asset)
    new_balance = current + amt
    set_wallet_balance(conn, addr, new_balance, asset)
    conn.commit()
    return new_balance


def apply_wallet_faucet_with_fee(
    conn: sqlite3.Connection,
    *,
    address: str,
    amount: int,
    fee_total: int,
    treasury_address: str,
    run_id: str,
    asset_id: str = "NYXT",
) -> dict[str, int]:
    addr = _validate_wallet_address(address)
    amt = _validate_int(amount, "amount", 1)
    fee = _validate_int(fee_total, "fee_total", 0)
    asset = _validate_text(asset_id, "asset_id", r"[A-Z0-9]{3,12}")
    treasury_addr = _validate_wallet_address(treasury_address, "treasury_address")
    
    _ensure_wallet_account(conn, addr, asset)
    _ensure_wallet_account(conn, treasury_addr, "NYXT")
    
    current = get_wallet_balance(conn, addr, asset)
    treasury_current = get_wallet_balance(conn, treasury_addr, "NYXT")
    
    new_balance = current + amt
    new_treasury = treasury_current + fee
    
    set_wallet_balance(conn, addr, new_balance, asset)
    set_wallet_balance(conn, treasury_addr, new_treasury, "NYXT")
    
    transfer_id = _validate_text(f"faucet-{run_id}", "transfer_id")
    insert_wallet_transfer(
        conn,
        WalletTransfer(
            transfer_id=transfer_id,
            from_address="faucet",
            to_address=addr,
            asset_id=asset,
            amount=amt,
            fee_total=fee,
            treasury_address=treasury_addr,
            run_id=run_id,
        ),
    )
    conn.commit()
    return {"balance": new_balance, "treasury_balance": new_treasury}


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
