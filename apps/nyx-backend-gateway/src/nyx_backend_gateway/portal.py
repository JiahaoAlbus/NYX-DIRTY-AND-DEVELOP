from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any

from nyx_backend_gateway import auth
from nyx_backend_gateway.env import (
    get_portal_challenge_ttl_seconds,
    get_portal_session_secret,
    get_portal_session_ttl_seconds,
)
from nyx_backend_gateway.identifiers import wallet_address as derive_wallet_address
from nyx_backend_gateway.storage import (
    ChatMessage,
    ChatRoom,
    PortalAccount,
    PortalChallenge,
    PortalSession,
    consume_portal_challenge,
    insert_chat_message,
    insert_chat_room,
    insert_portal_account,
    insert_portal_challenge,
    insert_portal_session,
    list_chat_messages,
    load_portal_account,
    load_portal_account_by_handle,
    load_portal_session,
)


class PortalError(ValueError):
    pass


def _canonical_json(value: dict[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _derive_account_id(handle: str, pubkey: str) -> str:
    digest = _sha256_hex(f"portal:acct:{handle}:{pubkey}".encode("utf-8"))
    return f"acct-{digest[:16]}"


def _validate_handle(handle: object) -> str:
    if not isinstance(handle, str) or not handle or isinstance(handle, bool):
        raise PortalError("handle required")
    if len(handle) < 3 or len(handle) > 24:
        raise PortalError("handle length invalid")
    if not all(ch.islower() or ch.isdigit() or ch in {"_", "-"} for ch in handle):
        raise PortalError("handle invalid")
    return handle


def _validate_pubkey(pubkey: object) -> str:
    if not isinstance(pubkey, str) or not pubkey or isinstance(pubkey, bool):
        raise PortalError("pubkey required")
    if len(pubkey) > 256:
        raise PortalError("pubkey too long")
    try:
        raw = base64.b64decode(pubkey.encode("utf-8"), validate=True)
    except Exception as exc:
        raise PortalError("pubkey invalid") from exc
    if len(raw) < 16:
        raise PortalError("pubkey invalid")
    return pubkey


def create_account(conn, handle: str, pubkey: str) -> PortalAccount:
    safe_handle = _validate_handle(handle)
    safe_pubkey = _validate_pubkey(pubkey)
    existing = load_portal_account_by_handle(conn, safe_handle)
    if existing is not None:
        raise PortalError("handle unavailable")
    account_id = _derive_account_id(safe_handle, safe_pubkey)
    created_at = int(time.time())
    wallet_addr = derive_wallet_address(account_id)
    account = PortalAccount(
        account_id=account_id,
        handle=safe_handle,
        public_key=safe_pubkey,
        wallet_address=wallet_addr,
        created_at=created_at,
        status="active",
    )
    insert_portal_account(conn, account)
    return account


def load_account(conn, account_id: str) -> PortalAccount | None:
    return load_portal_account(conn, account_id)


def issue_challenge(conn, account_id: str) -> PortalChallenge:
    account = load_portal_account(conn, account_id)
    if account is None:
        raise PortalError("account not found")
    secret = get_portal_session_secret()
    issued_at = int(time.time())
    entropy = os.urandom(16).hex()
    nonce = _sha256_hex(f"nonce:{account_id}:{issued_at}:{secret}:{entropy}".encode("utf-8"))
    ttl = get_portal_challenge_ttl_seconds()
    challenge = PortalChallenge(
        account_id=account.account_id,
        nonce=nonce,
        expires_at=issued_at + ttl,
        used=0,
    )
    insert_portal_challenge(conn, challenge)
    return challenge


def _verify_signature(pubkey: str, nonce: str, signature_b64: str) -> bool:
    try:
        key = base64.b64decode(pubkey.encode("utf-8"), validate=True)
    except Exception:
        return False
    try:
        provided = base64.b64decode(signature_b64.encode("utf-8"), validate=True)
    except Exception:
        return False
    expected = hmac.new(key, nonce.encode("utf-8"), hashlib.sha256).digest()
    return hmac.compare_digest(expected, provided)


def verify_challenge(conn, account_id: str, nonce: str, signature: str) -> PortalSession:
    challenge = consume_portal_challenge(conn, account_id, nonce)
    if challenge is None:
        raise PortalError("challenge not found")
    if challenge.used:
        raise PortalError("challenge already used")
    if int(time.time()) > challenge.expires_at:
        raise PortalError("challenge expired")
    account = load_portal_account(conn, account_id)
    if account is None:
        raise PortalError("account not found")
    if not _verify_signature(account.public_key, nonce, signature):
        raise PortalError("signature invalid")
    secret = get_portal_session_secret()
    expires_at = int(time.time()) + get_portal_session_ttl_seconds()
    session_id = auth.generate_session_id()
    token = auth.issue_token(
        account_id=account_id,
        session_id=session_id,
        expires_at=expires_at,
        secret=secret,
    )
    session = PortalSession(token=token, account_id=account_id, expires_at=expires_at)
    insert_portal_session(conn, session)
    return session


def require_session(conn, token: str) -> PortalSession:
    secret = get_portal_session_secret()
    try:
        payload = auth.verify_token(token, secret)
    except auth.AuthError as exc:
        raise PortalError(str(exc)) from exc
    session = load_portal_session(conn, token)
    if session is None:
        raise PortalError("session not found")
    if session.account_id != payload.account_id:
        raise PortalError("session account mismatch")
    if int(time.time()) > session.expires_at:
        raise PortalError("session expired")
    return session


def logout_session(conn, token: str) -> None:
    from nyx_backend_gateway.storage import delete_portal_session

    delete_portal_session(conn, token)


def update_profile(conn, account_id: str, handle: str | None = None, bio: str | None = None) -> PortalAccount:
    account = load_account(conn, account_id)
    if account is None:
        raise PortalError("account not found")

    new_handle = account.handle
    if handle is not None:
        new_handle = _validate_handle(handle)
        if new_handle != account.handle:
            existing = load_portal_account_by_handle(conn, new_handle)
            if existing is not None:
                raise PortalError("handle unavailable")

    new_bio = bio if bio is not None else account.bio
    if new_bio is not None and len(new_bio) > 256:
        raise PortalError("bio too long")

    conn.execute(
        "UPDATE portal_accounts SET handle = ?, bio = ? WHERE account_id = ?",
        (new_handle, new_bio, account_id),
    )
    conn.commit()
    return load_account(conn, account_id)  # type: ignore


def create_room(conn, name: str, is_public: bool = True) -> ChatRoom:
    if not isinstance(name, str) or not name or len(name) > 48:
        raise PortalError("room name invalid")
    created_at = int(time.time())
    room_id = f"room-{_sha256_hex(f'{name}:{created_at}'.encode('utf-8'))[:12]}"
    room = ChatRoom(room_id=room_id, name=name, created_at=created_at, is_public=1 if is_public else 0)
    insert_chat_room(conn, room)
    return room


def list_rooms(conn, limit: int = 50, offset: int = 0) -> list[dict[str, object]]:
    from nyx_backend_gateway.storage import _validate_int

    lim = _validate_int(limit, "limit", 1, 500)
    off = _validate_int(offset, "offset", 0)
    rows = conn.execute(
        "SELECT room_id, name, created_at, is_public FROM chat_rooms ORDER BY created_at ASC, room_id ASC LIMIT ? OFFSET ?",
        (lim, off),
    ).fetchall()
    return [{col: row[col] for col in row.keys()} for row in rows]


def search_rooms(conn, query: str, limit: int = 50) -> list[dict[str, object]]:
    from nyx_backend_gateway.storage import _validate_int

    lim = _validate_int(limit, "limit", 1, 500)
    rows = conn.execute(
        "SELECT room_id, name, created_at, is_public FROM chat_rooms WHERE name LIKE ? ORDER BY created_at ASC LIMIT ?",
        (f"%{query}%", lim),
    ).fetchall()
    return [{col: row[col] for col in row.keys()} for row in rows]


def post_message(conn, room_id: str, sender_account_id: str, body: str) -> tuple[dict[str, object], dict[str, object]]:
    if not isinstance(body, str) or not body or len(body) > 512:
        raise PortalError("message invalid")
    try:
        parsed = json.loads(body)
    except json.JSONDecodeError as exc:
        raise PortalError("message must be e2ee json") from exc
    if not isinstance(parsed, dict):
        raise PortalError("message must be e2ee json")
    if not isinstance(parsed.get("ciphertext"), str) or not parsed.get("ciphertext"):
        raise PortalError("message missing ciphertext")
    if not isinstance(parsed.get("iv"), str) or not parsed.get("iv"):
        raise PortalError("message missing iv")
    last = conn.execute(
        "SELECT seq, chain_head FROM chat_messages WHERE room_id = ? ORDER BY seq DESC LIMIT 1",
        (room_id,),
    ).fetchone()
    if last:
        prev_digest = str(last["chain_head"])
        seq = int(last["seq"]) + 1
    else:
        prev_digest = "0" * 64
        seq = 1
    message_id = f"msg-{_sha256_hex(f'{room_id}:{seq}'.encode('utf-8'))[:12]}"
    message_fields = {
        "message_id": message_id,
        "room_id": room_id,
        "sender_account_id": sender_account_id,
        "body": body,
        "seq": seq,
    }
    msg_digest = _sha256_hex(_canonical_json(message_fields).encode("utf-8"))
    chain_head = _sha256_hex(f"{prev_digest}{msg_digest}".encode("utf-8"))
    created_at = int(time.time())
    record = ChatMessage(
        message_id=message_id,
        room_id=room_id,
        sender_account_id=sender_account_id,
        body=body,
        seq=seq,
        prev_digest=prev_digest,
        msg_digest=msg_digest,
        chain_head=chain_head,
        created_at=created_at,
    )
    insert_chat_message(conn, record)
    receipt: dict[str, object] = {
        "prev_digest": prev_digest,
        "msg_digest": msg_digest,
        "chain_head": chain_head,
    }
    return message_fields, receipt


def list_messages(conn, room_id: str, after: int | None, limit: int) -> list[dict[str, object]]:
    return list_chat_messages(conn, room_id=room_id, after=after, limit=limit)


def list_account_activity(
    conn,
    account_id: str,
    wallet_address: str,
    limit: int = 50,
    offset: int = 0,
) -> list[dict[str, object]]:
    # Search across receipts linked to this account
    # For now, we'll return receipts that have a run_id matching transactions/orders for this account
    # In a real system, we'd have a join table or account_id on receipts
    rows = conn.execute(
        """
        SELECT
          r.receipt_id,
          r.module,
          r.action,
          r.state_hash,
          r.receipt_hashes,
          r.replay_ok,
          r.run_id,
          f.total_paid AS fee_total,
          f.protocol_fee_total AS protocol_fee_total,
          f.platform_fee_amount AS platform_fee_amount,
          f.fee_address AS treasury_address
        FROM receipts r
        LEFT JOIN fee_ledger f ON f.run_id = r.run_id
        WHERE r.run_id IN (
            SELECT run_id FROM wallet_transfers WHERE from_address = ? OR to_address = ?
            UNION
            SELECT run_id FROM orders WHERE owner_address = ?
            UNION
            SELECT run_id FROM messages WHERE sender_account_id = ?
            UNION
            SELECT run_id FROM listings WHERE publisher_id = ?
            UNION
            SELECT run_id FROM purchases WHERE buyer_id = ?
        )
        ORDER BY r.receipt_id DESC
        LIMIT ? OFFSET ?
        """,
        (
            wallet_address,
            wallet_address,
            wallet_address,
            account_id,
            wallet_address,
            wallet_address,
            limit,
            offset,
        ),
    ).fetchall()

    results = []
    for row in rows:
        record = {col: row[col] for col in row.keys()}
        try:
            record["receipt_hashes"] = json.loads(record.get("receipt_hashes", "[]"))
        except (TypeError, ValueError):
            record["receipt_hashes"] = []
        results.append(record)
    return results
