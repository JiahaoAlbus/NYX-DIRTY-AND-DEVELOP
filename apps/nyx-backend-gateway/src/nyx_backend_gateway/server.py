from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from nyx_backend_gateway.env import load_env_file
import nyx_backend_gateway.gateway as gateway
import nyx_backend_gateway.portal as portal
from nyx_backend_gateway.gateway import (
    GatewayError,
    execute_run,
    execute_wallet_faucet,
    execute_wallet_transfer,
    fetch_wallet_balance,
    _run_root,
    _db_path,
)
from nyx_backend_gateway.storage import (
    create_connection,
    list_entertainment_events,
    list_entertainment_items,
    list_listings,
    list_messages,
    list_orders,
    list_purchases,
    list_receipts,
    list_trades,
    load_by_id,
    StorageError,
)


_MAX_BODY = 4096
_RATE_LIMIT = 120
_RATE_WINDOW_SECONDS = 60
_ACCOUNT_RATE_LIMIT = 60


def _version_info() -> dict[str, str]:
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        commit = "unknown"
    try:
        describe = subprocess.check_output(["git", "describe", "--tags", "--always"], text=True).strip()
    except Exception:
        describe = "unknown"
    return {"commit": commit, "describe": describe, "build": "testnet"}


def _capabilities() -> dict[str, object]:
    return {
        "modules": {
            "portal": {"auth": "mandatory", "profile": "enabled"},
            "wallet": {"faucet": "enabled", "transfer": "enabled", "airdrop": "enabled"},
            "exchange": {"trading": "enabled", "orderbook": "enabled"},
            "marketplace": {"listing": "enabled", "purchase": "enabled"},
            "chat": {"e2ee": "verified", "rooms": "enabled"},
            "dapp": {"browser": "disabled"},
        }
    }


def _fee_summary(module: str, action: str, payload: dict, run_id: str) -> dict[str, object]:
    from nyx_backend_gateway.fees import route_fee

    record = route_fee(module, action, payload, run_id)
    return {
        "fee_total": record.total_paid,
        "fee_breakdown": {
            "protocol_fee_total": record.protocol_fee_total,
            "platform_fee_amount": record.platform_fee_amount,
        },
        "payer": "testnet-payer",
        "treasury_address": record.fee_address,
    }


class RequestLimiter:
    def __init__(self, limit: int, window_seconds: int) -> None:
        self._limit = limit
        self._window = window_seconds
        self._state: dict[str, tuple[int, float]] = {}

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        count, start = self._state.get(key, (0, now))
        if now - start >= self._window:
            count, start = 0, now
        if count >= self._limit:
            self._state[key] = (count, start)
            return False
        self._state[key] = (count + 1, start)
        return True


class GatewayHandler(BaseHTTPRequestHandler):
    server_version = "NYXGateway/2.0"

    def _send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        try:
            data = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
            self.end_headers()
            self.wfile.write(data)
        except Exception as exc:
            # Fallback for serialization errors
            error_data = json.dumps({"error": "internal serialization error"}).encode("utf-8")
            self.send_response(HTTPStatus.INTERNAL_SERVER_ERROR)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(error_data)))
            self.end_headers()
            self.wfile.write(error_data)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def _send_text(self, payload: str, status: HTTPStatus) -> None:
        data = payload.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_bytes(self, data: bytes, content_type: str) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _parse_body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        if length > _MAX_BODY:
            raise GatewayError("payload too large")
        body = self.rfile.read(length)
        try:
            payload = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            raise GatewayError("invalid json")
        if not isinstance(payload, dict):
            raise GatewayError("payload must be object")
        return payload

    def _rate_limit_ok(self) -> bool:
        limiter = getattr(self.server, "rate_limiter", None)
        if limiter is None:
            return True
        client = self.client_address[0] if self.client_address else "unknown"
        return limiter.allow(client)

    def _account_rate_limit_ok(self, account_id: str) -> bool:
        limiter = getattr(self.server, "account_limiter", None)
        if limiter is None:
            return True
        return limiter.allow(account_id)

    def _require_run_id(self, payload: dict) -> str:
        run_id = payload.get("run_id")
        if not isinstance(run_id, str) or not run_id or isinstance(run_id, bool):
            raise GatewayError("run_id required")
        return run_id

    def _require_seed(self, payload: dict) -> int:
        seed = payload.get("seed")
        if not isinstance(seed, int) or isinstance(seed, bool):
            raise GatewayError("seed must be int")
        return seed

    def _require_query_run_id(self, query: dict[str, list[str]]) -> str:
        run_id = (query.get("run_id") or [""])[0]
        if not run_id:
            raise GatewayError("run_id required")
        return run_id

    def _require_auth(self) -> portal.PortalSession:
        auth = self.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            raise GatewayError("auth required")
        token = auth.split(" ", 1)[1].strip()
        if not token:
            raise GatewayError("auth required")
        conn = create_connection(_db_path())
        try:
            session = portal.require_session(conn, token)
        except portal.PortalError as exc:
            raise GatewayError(str(exc)) from exc
        finally:
            conn.close()
        if not self._account_rate_limit_ok(session.account_id):
            raise GatewayError("rate limit exceeded")
        return session

    def do_POST(self) -> None:  # noqa: N802
        if not self._rate_limit_ok():
            self._send_text("rate limit exceeded", HTTPStatus.TOO_MANY_REQUESTS)
            return
        try:
            if self.path == "/run":
                session = self._require_auth()
                payload = self._parse_body()
                seed = self._require_seed(payload)
                run_id = self._require_run_id(payload)
                module = payload.get("module")
                action = payload.get("action")
                extra = payload.get("payload")
                result = execute_run(
                    seed=seed,
                    run_id=run_id,
                    module=module,
                    action=action,
                    payload=extra,
                    caller_account_id=session.account_id,
                )
                response = {
                    "run_id": result.run_id,
                    "status": "complete",
                    "state_hash": result.state_hash,
                    "receipt_hashes": result.receipt_hashes,
                    "replay_ok": result.replay_ok,
                }
                if isinstance(module, str) and isinstance(action, str) and isinstance(extra, dict):
                    if (module, action) in {
                        ("exchange", "route_swap"),
                        ("exchange", "place_order"),
                        ("exchange", "cancel_order"),
                        ("marketplace", "order_intent"),
                        ("marketplace", "listing_publish"),
                        ("marketplace", "purchase_listing"),
                    }:
                        response.update(_fee_summary(module, action, extra, result.run_id))
                self._send_json(response)
                return
            if self.path == "/portal/v1/accounts":
                payload = self._parse_body()
                conn = create_connection(_db_path())
                try:
                    account = portal.create_account(conn, payload.get("handle"), payload.get("pubkey"))
                finally:
                    conn.close()
                self._send_json(
                    {
                        "account_id": account.account_id,
                        "handle": account.handle,
                        "pubkey": account.public_key,
                        "created_at": account.created_at,
                        "status": account.status,
                    }
                )
                return
            if self.path == "/portal/v1/auth/challenge":
                payload = self._parse_body()
                account_id = payload.get("account_id")
                if not isinstance(account_id, str) or not account_id:
                    raise GatewayError("account_id required")
                conn = create_connection(_db_path())
                try:
                    challenge = portal.issue_challenge(conn, account_id)
                finally:
                    conn.close()
                self._send_json({"nonce": challenge.nonce, "expires_at": challenge.expires_at})
                return
            if self.path == "/portal/v1/auth/verify":
                payload = self._parse_body()
                account_id = payload.get("account_id")
                nonce = payload.get("nonce")
                signature = payload.get("signature")
                if not isinstance(account_id, str) or not account_id:
                    raise GatewayError("account_id required")
                if not isinstance(nonce, str) or not nonce:
                    raise GatewayError("nonce required")
                if not isinstance(signature, str) or not signature:
                    raise GatewayError("signature required")
                conn = create_connection(_db_path())
                try:
                    session = portal.verify_challenge(conn, account_id, nonce, signature)
                finally:
                    conn.close()
                self._send_json({"access_token": session.token, "expires_at": session.expires_at})
                return
            if self.path == "/portal/v1/auth/logout":
                session = self._require_auth()
                conn = create_connection(_db_path())
                try:
                    portal.logout_session(conn, session.token)
                finally:
                    conn.close()
                self._send_json({"ok": True})
                return
            if self.path == "/portal/v1/profile":
                session = self._require_auth()
                payload = self._parse_body()
                conn = create_connection(_db_path())
                try:
                    account = portal.update_profile(
                        conn, session.account_id, handle=payload.get("handle"), bio=payload.get("bio")
                    )
                finally:
                    conn.close()
                self._send_json({"account": account})
                return
            if self.path == "/chat/v1/rooms":
                _ = self._require_auth()
                payload = self._parse_body()
                name = payload.get("name")
                is_public = payload.get("is_public", True)
                conn = create_connection(_db_path())
                try:
                    room = portal.create_room(conn, name=name, is_public=bool(is_public))
                finally:
                    conn.close()
                self._send_json(
                    {
                        "room_id": room.room_id,
                        "name": room.name,
                        "created_at": room.created_at,
                        "is_public": bool(room.is_public),
                    }
                )
                return
            if self.path.startswith("/chat/v1/rooms/") and self.path.endswith("/messages"):
                parts = self.path.split("/")
                if len(parts) != 6:
                    raise GatewayError("room_id required")
                room_id = parts[4]
                session = self._require_auth()
                payload = self._parse_body()
                body = payload.get("body")
                if not isinstance(body, str) or not body:
                    raise GatewayError("body required")
                conn = create_connection(_db_path())
                try:
                    message_fields, receipt = portal.post_message(
                        conn, room_id=room_id, sender_account_id=session.account_id, body=body
                    )
                finally:
                    conn.close()
                self._send_json({"message": message_fields, "receipt": receipt})
                return
            if self.path == "/wallet/v1/faucet":
                session = self._require_auth()
                payload = self._parse_body()
                seed = self._require_seed(payload)
                run_id = self._require_run_id(payload)
                faucet_payload = payload.get("payload")
                if faucet_payload is None:
                    faucet_payload = {k: v for k, v in payload.items() if k not in {"seed", "run_id"}}
                result, balance, fee_record = gateway.execute_wallet_faucet_v1(
                    seed=seed,
                    run_id=run_id,
                    payload=faucet_payload,
                    account_id=session.account_id,
                )
                self._send_json(
                    {
                        "run_id": result.run_id,
                        "status": "complete",
                        "state_hash": result.state_hash,
                        "receipt_hashes": result.receipt_hashes,
                        "replay_ok": result.replay_ok,
                        "address": faucet_payload.get("address"),
                        "balance": balance,
                        "fee_total": fee_record.total_paid,
                        "fee_breakdown": {
                            "protocol_fee_total": fee_record.protocol_fee_total,
                            "platform_fee_amount": fee_record.platform_fee_amount,
                        },
                        "payer": session.account_id,
                        "treasury_address": fee_record.fee_address,
                    }
                )
                return
            if self.path == "/wallet/v1/transfer":
                session = self._require_auth()
                payload = self._parse_body()
                seed = self._require_seed(payload)
                run_id = self._require_run_id(payload)
                transfer_payload = payload.get("payload")
                if transfer_payload is None:
                    transfer_payload = {k: v for k, v in payload.items() if k not in {"seed", "run_id"}}
                result, balances, fee_record = execute_wallet_transfer(
                    seed=seed,
                    run_id=run_id,
                    payload=transfer_payload,
                )
                self._send_json(
                    {
                        "run_id": result.run_id,
                        "status": "complete",
                        "state_hash": result.state_hash,
                        "receipt_hashes": result.receipt_hashes,
                        "replay_ok": result.replay_ok,
                        "from_address": transfer_payload.get("from_address"),
                        "to_address": transfer_payload.get("to_address"),
                        "amount": transfer_payload.get("amount"),
                        "fee_total": fee_record.total_paid,
                        "fee_breakdown": {
                            "protocol_fee_total": fee_record.protocol_fee_total,
                            "platform_fee_amount": fee_record.platform_fee_amount,
                        },
                        "payer": session.account_id,
                        "treasury_address": fee_record.fee_address,
                        "from_balance": balances["from_balance"],
                        "to_balance": balances["to_balance"],
                        "treasury_balance": balances["treasury_balance"],
                    }
                )
                return
            if self.path == "/exchange/place_order":
                payload = self._parse_body()
                seed = self._require_seed(payload)
                run_id = self._require_run_id(payload)
                order_payload = payload.get("payload")
                if order_payload is None:
                    order_payload = {k: v for k, v in payload.items() if k not in {"seed", "run_id"}}
                result = execute_run(
                    seed=seed,
                    run_id=run_id,
                    module="exchange",
                    action="place_order",
                    payload=order_payload,
                )
                response = {
                    "run_id": result.run_id,
                    "status": "complete",
                    "state_hash": result.state_hash,
                    "receipt_hashes": result.receipt_hashes,
                    "replay_ok": result.replay_ok,
                }
                if isinstance(order_payload, dict):
                    response.update(_fee_summary("exchange", "place_order", order_payload, result.run_id))
                self._send_json(response)
                return
            if self.path == "/exchange/cancel_order":
                payload = self._parse_body()
                seed = self._require_seed(payload)
                run_id = self._require_run_id(payload)
                cancel_payload = payload.get("payload")
                if cancel_payload is None:
                    cancel_payload = {k: v for k, v in payload.items() if k not in {"seed", "run_id"}}
                result = execute_run(
                    seed=seed,
                    run_id=run_id,
                    module="exchange",
                    action="cancel_order",
                    payload=cancel_payload,
                )
                response = {
                    "run_id": result.run_id,
                    "status": "complete",
                    "state_hash": result.state_hash,
                    "receipt_hashes": result.receipt_hashes,
                    "replay_ok": result.replay_ok,
                }
                if isinstance(cancel_payload, dict):
                    response.update(_fee_summary("exchange", "cancel_order", cancel_payload, result.run_id))
                self._send_json(response)
                return
            if self.path == "/chat/send":
                payload = self._parse_body()
                seed = self._require_seed(payload)
                run_id = self._require_run_id(payload)
                message_payload = payload.get("payload")
                if message_payload is None:
                    message_payload = {k: v for k, v in payload.items() if k not in {"seed", "run_id"}}
                result = execute_run(
                    seed=seed,
                    run_id=run_id,
                    module="chat",
                    action="message_event",
                    payload=message_payload,
                )
                self._send_json(
                    {
                        "run_id": result.run_id,
                        "status": "complete",
                        "state_hash": result.state_hash,
                        "receipt_hashes": result.receipt_hashes,
                        "replay_ok": result.replay_ok,
                    }
                )
                return
            if self.path in {"/wallet/faucet", "/wallet/v1/faucet"}:
                payload = self._parse_body()
                seed = self._require_seed(payload)
                run_id = self._require_run_id(payload)
                faucet_payload = payload.get("payload")
                if faucet_payload is None:
                    faucet_payload = {k: v for k, v in payload.items() if k not in {"seed", "run_id"}}
                result, balances, fee_record = execute_wallet_faucet(
                    seed=seed,
                    run_id=run_id,
                    payload=faucet_payload,
                )
                self._send_json(
                    {
                        "run_id": result.run_id,
                        "status": "complete",
                        "state_hash": result.state_hash,
                        "receipt_hashes": result.receipt_hashes,
                        "replay_ok": result.replay_ok,
                        "address": faucet_payload.get("address"),
                        "balance": balances["balance"],
                    }
                )
                return
            if self.path in {"/wallet/airdrop/claim", "/wallet/v1/airdrop/claim"}:
                payload = self._parse_body()
                seed = self._require_seed(payload)
                run_id = self._require_run_id(payload)
                claim_payload = payload.get("payload")
                if claim_payload is None:
                    claim_payload = {k: v for k, v in payload.items() if k not in {"seed", "run_id"}}
                result, balances, fee_record = execute_airdrop_claim(
                    seed=seed,
                    run_id=run_id,
                    payload=claim_payload,
                )
                self._send_json(
                    {
                        "run_id": result.run_id,
                        "status": "complete",
                        "state_hash": result.state_hash,
                        "receipt_hashes": result.receipt_hashes,
                        "replay_ok": result.replay_ok,
                        "address": claim_payload.get("address"),
                        "task_id": claim_payload.get("task_id"),
                        "balance": balances["balance"],
                        "fee_total": fee_record.total_paid,
                    }
                )
                return
            if self.path in {"/wallet/transfer", "/wallet/v1/transfer"}:
                payload = self._parse_body()
                seed = self._require_seed(payload)
                run_id = self._require_run_id(payload)
                transfer_payload = payload.get("payload")
                if transfer_payload is None:
                    transfer_payload = {k: v for k, v in payload.items() if k not in {"seed", "run_id"}}
                result, balances, fee_record = execute_wallet_transfer(
                    seed=seed,
                    run_id=run_id,
                    payload=transfer_payload,
                )
                self._send_json(
                    {
                        "run_id": result.run_id,
                        "status": "complete",
                        "state_hash": result.state_hash,
                        "receipt_hashes": result.receipt_hashes,
                        "replay_ok": result.replay_ok,
                        "from_address": transfer_payload.get("from_address"),
                        "to_address": transfer_payload.get("to_address"),
                        "amount": transfer_payload.get("amount"),
                        "fee_total": fee_record.total_paid,
                        "fee_breakdown": {
                            "protocol_fee_total": fee_record.protocol_fee_total,
                            "platform_fee_amount": fee_record.platform_fee_amount,
                        },
                        "payer": transfer_payload.get("from_address"),
                        "treasury_address": fee_record.fee_address,
                        "from_balance": balances["from_balance"],
                        "to_balance": balances["to_balance"],
                        "treasury_balance": balances["treasury_balance"],
                    }
                )
                return
            if self.path == "/marketplace/listing":
                payload = self._parse_body()
                seed = self._require_seed(payload)
                run_id = self._require_run_id(payload)
                listing_payload = payload.get("payload")
                if listing_payload is None:
                    listing_payload = {k: v for k, v in payload.items() if k not in {"seed", "run_id"}}
                result = execute_run(
                    seed=seed,
                    run_id=run_id,
                    module="marketplace",
                    action="listing_publish",
                    payload=listing_payload,
                )
                response = {
                    "run_id": result.run_id,
                    "status": "complete",
                    "state_hash": result.state_hash,
                    "receipt_hashes": result.receipt_hashes,
                    "replay_ok": result.replay_ok,
                }
                if isinstance(listing_payload, dict):
                    response.update(_fee_summary("marketplace", "listing_publish", listing_payload, result.run_id))
                self._send_json(response)
                return
            if self.path == "/marketplace/purchase":
                payload = self._parse_body()
                seed = self._require_seed(payload)
                run_id = self._require_run_id(payload)
                purchase_payload = payload.get("payload")
                if purchase_payload is None:
                    purchase_payload = {k: v for k, v in payload.items() if k not in {"seed", "run_id"}}
                result = execute_run(
                    seed=seed,
                    run_id=run_id,
                    module="marketplace",
                    action="purchase_listing",
                    payload=purchase_payload,
                )
                response = {
                    "run_id": result.run_id,
                    "status": "complete",
                    "state_hash": result.state_hash,
                    "receipt_hashes": result.receipt_hashes,
                    "replay_ok": result.replay_ok,
                }
                if isinstance(purchase_payload, dict):
                    response.update(_fee_summary("marketplace", "purchase_listing", purchase_payload, result.run_id))
                self._send_json(response)
                return
            if self.path == "/entertainment/step":
                payload = self._parse_body()
                seed = self._require_seed(payload)
                run_id = self._require_run_id(payload)
                step_payload = payload.get("payload")
                if step_payload is None:
                    step_payload = {k: v for k, v in payload.items() if k not in {"seed", "run_id"}}
                result = execute_run(
                    seed=seed,
                    run_id=run_id,
                    module="entertainment",
                    action="state_step",
                    payload=step_payload,
                )
                self._send_json(
                    {
                        "run_id": result.run_id,
                        "status": "complete",
                        "state_hash": result.state_hash,
                        "receipt_hashes": result.receipt_hashes,
                        "replay_ok": result.replay_ok,
                    }
                )
                return
            self._send_text("not found", HTTPStatus.NOT_FOUND)
        except (GatewayError, portal.PortalError, StorageError) as exc:
            self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)

    def do_GET(self) -> None:  # noqa: N802
        if not self._rate_limit_ok():
            self._send_text("rate limit exceeded", HTTPStatus.TOO_MANY_REQUESTS)
            return
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        if path == "/discovery/feed":
            try:
                conn = create_connection(_db_path())
                # Mix of rooms and listings
                rooms = portal.list_rooms(conn, limit=5)
                listings = gateway.marketplace_list_active_listings(conn, limit=5)
                conn.close()
                self._send_json({
                    "feed": [
                        {"type": "room", "data": r} for r in rooms
                    ] + [
                        {"type": "listing", "data": l} for l in listings
                    ]
                })
            except Exception as exc:
                self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        if path == "/healthz":
            self._send_json({"ok": True})
            return
        if path == "/version":
            self._send_json(_version_info())
            return
        if path == "/capabilities":
            self._send_json(_capabilities())
            return
        if path == "/portal/v1/me":
            try:
                session = self._require_auth()
                conn = create_connection(_db_path())
                account = portal.load_account(conn, session.account_id)
                conn.close()
                if account is None:
                    raise GatewayError("account not found")
                self._send_json(
                    {
                        "account_id": account.account_id,
                        "handle": account.handle,
                        "pubkey": account.public_key,
                        "created_at": account.created_at,
                        "status": account.status,
                    }
                )
            except GatewayError as exc:
                self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        if path == "/portal/v1/activity":
            try:
                session = self._require_auth()
                limit_raw = (query.get("limit") or ["50"])[0]
                offset_raw = (query.get("offset") or ["0"])[0]
                try:
                    limit = int(limit_raw)
                    offset = int(offset_raw)
                except ValueError:
                    raise GatewayError("limit or offset invalid")
                conn = create_connection(_db_path())
                receipts = portal.list_account_activity(conn, session.account_id, limit=limit, offset=offset)
                conn.close()
                self._send_json({"account_id": session.account_id, "receipts": receipts, "limit": limit, "offset": offset})
            except (GatewayError, portal.PortalError, StorageError) as exc:
                self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        if path == "/status":
            try:
                run_id = self._require_query_run_id(query)
                from nyx_backend.evidence import EvidenceError, load_evidence

                evidence = load_evidence(run_id, base_dir=_run_root())
                self._send_json({"status": "complete", "replay_ok": evidence.replay_ok})
            except EvidenceError as exc:
                self._send_json({"status": "error", "error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        if path == "/evidence":
            try:
                run_id = self._require_query_run_id(query)
                from nyx_backend.evidence import EvidenceError, load_evidence

                evidence = load_evidence(run_id, base_dir=_run_root())
            except EvidenceError as exc:
                self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
                return
            payload = {
                "protocol_anchor": evidence.protocol_anchor,
                "inputs": evidence.inputs,
                "outputs": evidence.outputs,
                "receipt_hashes": evidence.receipt_hashes,
                "state_hash": evidence.state_hash,
                "replay_ok": evidence.replay_ok,
                "stdout": evidence.stdout,
            }
            self._send_json(payload)
            return
        if path == "/artifact":
            try:
                run_id = self._require_query_run_id(query)
                name = (query.get("name") or [""])[0]
                from nyx_backend.evidence import EvidenceError, _safe_artifact_path

                artifact_path = _safe_artifact_path(_run_root(), run_id, name)
                data = artifact_path.read_bytes()
            except EvidenceError as exc:
                self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
                return
            self._send_bytes(data, "application/octet-stream")
            return
        if path == "/export.zip":
            try:
                run_id = self._require_query_run_id(query)
                from nyx_backend.evidence import EvidenceError, build_export_zip

                data = build_export_zip(run_id, base_dir=_run_root())
            except EvidenceError as exc:
                self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
                return
            self._send_bytes(data, "application/zip")
            return
        if path == "/list":
            from nyx_backend.evidence import list_runs

            records = list_runs(base_dir=_run_root())
            payload = [{"run_id": record.run_id, "status": record.status} for record in records]
            self._send_json({"runs": payload})
            return
        if path == "/wallet/balance":
            try:
                address = (query.get("address") or [""])[0]
                balance = fetch_wallet_balance(address=address)
                self._send_json({"address": address, "balance": balance})
            except Exception as exc:
                self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        if path == "/exchange/orders":
            try:
                conn = create_connection(_db_path())
                side = (query.get("side") or [""])[0] or None
                asset_in = (query.get("asset_in") or [""])[0] or None
                asset_out = (query.get("asset_out") or [""])[0] or None
                limit = int((query.get("limit") or ["100"])[0])
                offset = int((query.get("offset") or ["0"])[0])
                orders = list_orders(conn, side=side, asset_in=asset_in, asset_out=asset_out, limit=limit, offset=offset)
                conn.close()
                self._send_json({"orders": orders, "limit": limit, "offset": offset})
            except Exception as exc:
                self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        if path == "/exchange/trades":
            try:
                conn = create_connection(_db_path())
                limit = int((query.get("limit") or ["100"])[0])
                offset = int((query.get("offset") or ["0"])[0])
                trades = list_trades(conn, limit=limit, offset=offset)
                conn.close()
                self._send_json({"trades": trades, "limit": limit, "offset": offset})
            except Exception as exc:
                self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        if path == "/exchange/orderbook":
            try:
                conn = create_connection(_db_path())
                buys = list_orders(conn, side="BUY", order_by="price DESC, order_id ASC")
                sells = list_orders(conn, side="SELL", order_by="price ASC, order_id ASC")
                conn.close()
                self._send_json({"buy": buys, "sell": sells})
            except Exception as exc:
                self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        if path == "/chat/messages":
            try:
                conn = create_connection(_db_path())
                channel = (query.get("channel") or [""])[0] or None
                limit = int((query.get("limit") or ["50"])[0])
                offset = int((query.get("offset") or ["0"])[0])
                messages = list_messages(conn, channel=channel, limit=limit, offset=offset)
                conn.close()
                self._send_json({"messages": messages, "limit": limit, "offset": offset})
            except Exception as exc:
                self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        if path == "/chat/v1/rooms":
            try:
                _ = self._require_auth()
                limit = int((query.get("limit") or ["50"])[0])
                offset = int((query.get("offset") or ["0"])[0])
                conn = create_connection(_db_path())
                rooms = portal.list_rooms(conn, limit=limit, offset=offset)
                conn.close()
                self._send_json({"rooms": rooms, "limit": limit, "offset": offset})
            except GatewayError as exc:
                self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        if path == "/portal/v1/rooms/search":
            try:
                _ = self._require_auth()
                q = (query.get("q") or [""])[0]
                conn = create_connection(_db_path())
                rooms = portal.search_rooms(conn, q)
                conn.close()
                self._send_json({"rooms": rooms})
            except Exception as exc:
                self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        if path.startswith("/chat/v1/rooms/") and path.endswith("/messages"):
            parts = path.split("/")
            if len(parts) != 6:
                self._send_text("not found", HTTPStatus.NOT_FOUND)
                return
            room_id = parts[4]
            try:
                _ = self._require_auth()
                after_raw = (query.get("after") or [""])[0] or None
                limit_raw = (query.get("limit") or [""])[0] or None
                after = int(after_raw) if after_raw else None
                limit = int(limit_raw) if limit_raw else 50
                conn = create_connection(_db_path())
                messages = portal.list_messages(conn, room_id=room_id, after=after, limit=limit)
                conn.close()
                self._send_json({"messages": messages})
            except Exception as exc:
                self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        if path == "/marketplace/listings":
            try:
                conn = create_connection(_db_path())
                listings = gateway.marketplace_list_active_listings(conn)
                conn.close()
                self._send_json({"listings": listings})
            except Exception as exc:
                self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        if path == "/marketplace/listings/search":
            try:
                q = (query.get("q") or [""])[0]
                conn = create_connection(_db_path())
                listings = gateway.marketplace_search_listings(conn, q)
                conn.close()
                self._send_json({"listings": listings})
            except Exception as exc:
                self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        if path == "/marketplace/purchases":
            try:
                conn = create_connection(_db_path())
                listing_id = (query.get("listing_id") or [""])[0] or None
                limit = int((query.get("limit") or ["100"])[0])
                offset = int((query.get("offset") or ["0"])[0])
                purchases = list_purchases(conn, listing_id=listing_id, limit=limit, offset=offset)
                conn.close()
                self._send_json({"purchases": purchases, "limit": limit, "offset": offset})
            except Exception as exc:
                self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        if path == "/entertainment/items":
            try:
                conn = create_connection(_db_path())
                gateway._ensure_entertainment_items(conn)
                limit = int((query.get("limit") or ["100"])[0])
                offset = int((query.get("offset") or ["0"])[0])
                items = list_entertainment_items(conn, limit=limit, offset=offset)
                conn.close()
                self._send_json({"items": items, "limit": limit, "offset": offset})
            except Exception as exc:
                self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        if path == "/entertainment/events":
            try:
                conn = create_connection(_db_path())
                item_id = (query.get("item_id") or [""])[0] or None
                limit = int((query.get("limit") or ["100"])[0])
                offset = int((query.get("offset") or ["0"])[0])
                events = list_entertainment_events(conn, item_id=item_id, limit=limit, offset=offset)
                conn.close()
                self._send_json({"events": events, "limit": limit, "offset": offset})
            except Exception as exc:
                self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        self._send_text("not found", HTTPStatus.NOT_FOUND)


def run_server(host: str = "0.0.0.0", port: int = 8091) -> None:
    server = ThreadingHTTPServer((host, port), GatewayHandler)
    server.rate_limiter = RequestLimiter(_RATE_LIMIT, _RATE_WINDOW_SECONDS)
    server.account_limiter = RequestLimiter(_ACCOUNT_RATE_LIMIT, _RATE_WINDOW_SECONDS)
    server.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NYX backend gateway")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8091)
    parser.add_argument("--env-file", default="")
    args = parser.parse_args()
    if args.env_file:
        load_env_file(Path(args.env_file))
    run_server(host=args.host, port=args.port)
