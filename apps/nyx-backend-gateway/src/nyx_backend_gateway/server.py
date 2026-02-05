from __future__ import annotations

import argparse
import io
import json
from pathlib import Path
import re
import subprocess
import time
import zipfile
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from nyx_backend_gateway.env import load_env_file
import nyx_backend_gateway.gateway as gateway
import nyx_backend_gateway.portal as portal
from nyx_backend_gateway.gateway import (
    GatewayError,
    GatewayApiError,
    execute_run,
    execute_wallet_faucet,
    execute_wallet_transfer,
    fetch_wallet_balance,
    _run_root,
    _db_path,
)
from nyx_backend_gateway.storage import (
    create_connection,
    get_wallet_balance,
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
    from nyx_backend_gateway.env import (
        get_0x_api_key,
        get_jupiter_api_key,
    )

    integration_features = {
        "0x_quote": "enabled" if get_0x_api_key() else "disabled_missing_api_key",
        "jupiter_quote": "enabled" if get_jupiter_api_key() else "disabled_missing_api_key",
        "magic_eden_solana": "enabled",
        "magic_eden_evm": "enabled",
        # PayEVM is not shipped yet (NO FAKE UI).
        "payevm": "disabled_not_implemented",
    }
    module_features = {
        "portal": {"auth": "mandatory", "profile": "enabled"},
        "wallet": {"faucet": "enabled", "transfer": "enabled", "airdrop": "enabled"},
        "exchange": {"trading": "enabled", "orderbook": "enabled"},
        "marketplace": {"listing": "enabled", "purchase": "enabled"},
        "chat": {"e2ee": "verified", "dm": "enabled"},
        "dapp": {"browser": "enabled"},
        "web2": {"guard": "enabled"},
        "integrations": integration_features,
    }
    return {
        "modules": sorted(module_features.keys()),
        "module_features": module_features,
        "endpoints": [
            "/run",
            "/capabilities",
            "/portal/v1/me",
            "/portal/v1/activity",
            "/portal/v1/accounts/search",
            "/portal/v1/accounts/by_id",
            "/portal/v1/e2ee/identity",
            "/wallet/v1/balances",
            "/wallet/v1/transfers",
            "/wallet/v1/airdrop/tasks",
            "/wallet/v1/airdrop/claim",
            "/wallet/v1/faucet",
            "/wallet/v1/transfer",
            "/exchange/orderbook",
            "/exchange/v1/my_orders",
            "/exchange/v1/my_trades",
            "/marketplace/listings",
            "/marketplace/listings/search",
            "/marketplace/v1/my_purchases",
            "/chat/v1/conversations",
            "/chat/messages",
            "/integrations/v1/0x/quote",
            "/integrations/v1/jupiter/quote",
            "/integrations/v1/magic_eden/solana/collections",
            "/integrations/v1/magic_eden/solana/collection_listings",
            "/integrations/v1/magic_eden/solana/token",
            "/integrations/v1/magic_eden/evm/collections/search",
            "/integrations/v1/magic_eden/evm/collections",
            "/web2/v1/allowlist",
            "/web2/v1/request",
            "/web2/v1/requests",
            "/evidence",
            "/evidence/v1/replay",
            "/export.zip",
            "/proof.zip",
        ],
        "assets": gateway.supported_assets(),
        "exchange_pairs": [{"base": "ECHO", "quote": "NYXT", "status": "enabled"}],
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

    def _send_error(self, exc: Exception, status: HTTPStatus = HTTPStatus.BAD_REQUEST) -> None:
        if isinstance(exc, GatewayApiError):
            resolved = HTTPStatus.BAD_REQUEST
            try:
                resolved = HTTPStatus(exc.http_status)
            except ValueError:
                resolved = HTTPStatus.BAD_REQUEST
            self._send_json({"error": {"code": exc.code, "message": str(exc), "details": exc.details}}, resolved)
            return
        self._send_json({"error": {"code": "BAD_REQUEST", "message": str(exc)}}, status)

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
            raise GatewayApiError("AUTH_REQUIRED", "auth required", http_status=HTTPStatus.UNAUTHORIZED)
        token = auth.split(" ", 1)[1].strip()
        if not token:
            raise GatewayApiError("AUTH_REQUIRED", "auth required", http_status=HTTPStatus.UNAUTHORIZED)
        conn = create_connection(_db_path())
        try:
            session = portal.require_session(conn, token)
        except portal.PortalError as exc:
            raise GatewayApiError("AUTH_INVALID", str(exc), http_status=HTTPStatus.UNAUTHORIZED) from exc
        finally:
            conn.close()
        if not self._account_rate_limit_ok(session.account_id):
            raise GatewayApiError("ACCOUNT_RATE_LIMIT", "rate limit exceeded", http_status=HTTPStatus.TOO_MANY_REQUESTS)
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
                        ("chat", "message_event"),
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
            if self.path == "/portal/v1/e2ee/identity":
                session = self._require_auth()
                payload = self._parse_body()
                public_jwk = payload.get("public_jwk")
                jwk_obj: dict | None = None
                jwk_str: str | None = None
                if isinstance(public_jwk, dict):
                    jwk_obj = public_jwk
                    jwk_str = json.dumps(public_jwk, sort_keys=True, separators=(",", ":"))
                elif isinstance(public_jwk, str) and public_jwk.strip():
                    jwk_str = public_jwk.strip()
                    jwk_obj = json.loads(jwk_str)
                else:
                    raise GatewayError("public_jwk required")
                if not isinstance(jwk_obj, dict):
                    raise GatewayError("public_jwk invalid")
                if len(jwk_str or "") > 2048:
                    raise GatewayError("public_jwk too long")
                if not isinstance(jwk_obj.get("kty"), str) or not isinstance(jwk_obj.get("crv"), str):
                    raise GatewayError("public_jwk invalid")
                if not isinstance(jwk_obj.get("x"), str) or not isinstance(jwk_obj.get("y"), str):
                    raise GatewayError("public_jwk invalid")
                updated_at = int(time.time())
                conn = create_connection(_db_path())
                try:
                    conn.execute(
                        "INSERT OR REPLACE INTO e2ee_identities (account_id, public_jwk, updated_at) VALUES (?, ?, ?)",
                        (session.account_id, jwk_str, updated_at),
                    )
                    conn.commit()
                finally:
                    conn.close()
                self._send_json({"account_id": session.account_id, "public_jwk": jwk_obj, "updated_at": updated_at})
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
                client_ip = self.client_address[0] if self.client_address else None
                result, balance, fee_record = gateway.execute_wallet_faucet_v1(
                    seed=seed,
                    run_id=run_id,
                    payload=faucet_payload,
                    account_id=session.account_id,
                    client_ip=client_ip,
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
            if self.path == "/wallet/v1/airdrop/claim":
                session = self._require_auth()
                payload = self._parse_body()
                seed = self._require_seed(payload)
                run_id = self._require_run_id(payload)
                claim_payload = payload.get("payload")
                if claim_payload is None:
                    claim_payload = {k: v for k, v in payload.items() if k not in {"seed", "run_id"}}
                if not isinstance(claim_payload, dict):
                    raise GatewayError("payload must be object")
                result, balance, fee_record, claim = gateway.execute_airdrop_claim_v1(
                    seed=seed,
                    run_id=run_id,
                    payload=claim_payload,
                    account_id=session.account_id,
                )
                self._send_json(
                    {
                        "run_id": result.run_id,
                        "status": "complete",
                        "state_hash": result.state_hash,
                        "receipt_hashes": result.receipt_hashes,
                        "replay_ok": result.replay_ok,
                        "account_id": session.account_id,
                        "task_id": claim.get("task_id"),
                        "reward": claim.get("reward"),
                        "completion_run_id": claim.get("completion_run_id"),
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
                if not isinstance(transfer_payload, dict):
                    raise GatewayError("payload must be object")
                if transfer_payload.get("from_address") != session.account_id:
                    raise GatewayApiError(
                        "FROM_ADDRESS_MISMATCH",
                        "from_address must match authenticated account_id",
                        http_status=403,
                    )
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
                        "asset_id": transfer_payload.get("asset_id", "NYXT"),
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
                session = self._require_auth()
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
                    caller_account_id=session.account_id,
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
                session = self._require_auth()
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
                    caller_account_id=session.account_id,
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
                session = self._require_auth()
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
                    caller_account_id=session.account_id,
                )
                response = {
                    "run_id": result.run_id,
                    "status": "complete",
                    "state_hash": result.state_hash,
                    "receipt_hashes": result.receipt_hashes,
                    "replay_ok": result.replay_ok,
                }
                if isinstance(message_payload, dict):
                    response.update(_fee_summary("chat", "message_event", message_payload, result.run_id))
                self._send_json(response)
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
            if self.path == "/wallet/airdrop/claim":
                session = self._require_auth()
                payload = self._parse_body()
                seed = self._require_seed(payload)
                run_id = self._require_run_id(payload)
                claim_payload = payload.get("payload")
                if claim_payload is None:
                    claim_payload = {k: v for k, v in payload.items() if k not in {"seed", "run_id"}}
                if not isinstance(claim_payload, dict):
                    raise GatewayError("payload must be object")
                result, balance, fee_record, claim = gateway.execute_airdrop_claim_v1(
                    seed=seed,
                    run_id=run_id,
                    payload=claim_payload,
                    account_id=session.account_id,
                )
                self._send_json(
                    {
                        "run_id": result.run_id,
                        "status": "complete",
                        "state_hash": result.state_hash,
                        "receipt_hashes": result.receipt_hashes,
                        "replay_ok": result.replay_ok,
                        "account_id": session.account_id,
                        "task_id": claim.get("task_id"),
                        "reward": claim.get("reward"),
                        "completion_run_id": claim.get("completion_run_id"),
                        "balance": balance,
                        "fee_total": fee_record.total_paid,
                        "payer": session.account_id,
                        "treasury_address": fee_record.fee_address,
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
                session = self._require_auth()
                payload = self._parse_body()
                seed = self._require_seed(payload)
                run_id = self._require_run_id(payload)
                listing_payload = payload.get("payload")
                if listing_payload is None:
                    listing_payload = {k: v for k, v in payload.items() if k not in {"seed", "run_id"}}
                if isinstance(listing_payload, dict) and "publisher_id" not in listing_payload:
                    listing_payload["publisher_id"] = session.account_id
                result = execute_run(
                    seed=seed,
                    run_id=run_id,
                    module="marketplace",
                    action="listing_publish",
                    payload=listing_payload,
                    caller_account_id=session.account_id,
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
                session = self._require_auth()
                payload = self._parse_body()
                seed = self._require_seed(payload)
                run_id = self._require_run_id(payload)
                purchase_payload = payload.get("payload")
                if purchase_payload is None:
                    purchase_payload = {k: v for k, v in payload.items() if k not in {"seed", "run_id"}}
                if isinstance(purchase_payload, dict) and "buyer_id" not in purchase_payload:
                    purchase_payload["buyer_id"] = session.account_id
                result = execute_run(
                    seed=seed,
                    run_id=run_id,
                    module="marketplace",
                    action="purchase_listing",
                    payload=purchase_payload,
                    caller_account_id=session.account_id,
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
            if self.path == "/web2/v1/request":
                session = self._require_auth()
                payload = self._parse_body()
                seed = self._require_seed(payload)
                run_id = self._require_run_id(payload)
                web2_payload = payload.get("payload")
                if web2_payload is None:
                    web2_payload = {k: v for k, v in payload.items() if k not in {"seed", "run_id"}}
                if not isinstance(web2_payload, dict):
                    raise GatewayError("payload must be object")
                response = gateway.execute_web2_guard_request(
                    seed=seed,
                    run_id=run_id,
                    payload=web2_payload,
                    account_id=session.account_id,
                )
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
            if self.path == "/evidence/v1/replay":
                _ = self._require_auth()
                payload = self._parse_body()
                run_id = payload.get("run_id")
                if not isinstance(run_id, str) or not run_id or isinstance(run_id, bool):
                    raise GatewayError("run_id required")
                backend_src = gateway._backend_src()
                if str(backend_src) not in __import__("sys").path:
                    __import__("sys").path.insert(0, str(backend_src))
                from nyx_backend.evidence import EvidenceError, replay_verify_run

                try:
                    result = replay_verify_run(run_id, base_dir=_run_root())
                except EvidenceError as exc:
                    raise GatewayError(str(exc)) from exc
                self._send_json(result)
                return
            self._send_text("not found", HTTPStatus.NOT_FOUND)
        except (GatewayApiError, GatewayError, portal.PortalError, StorageError) as exc:
            self._send_error(exc, HTTPStatus.BAD_REQUEST)

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
        if path == "/web2/v1/allowlist":
            self._send_json({"allowlist": gateway.list_web2_allowlist()})
            return
        if path == "/web2/v1/requests":
            try:
                session = self._require_auth()
                limit_raw = (query.get("limit") or ["50"])[0]
                offset_raw = (query.get("offset") or ["0"])[0]
                try:
                    limit = int(limit_raw)
                    offset = int(offset_raw)
                except ValueError:
                    raise GatewayError("limit or offset invalid")
                rows = gateway.fetch_web2_guard_requests(
                    account_id=session.account_id,
                    limit=limit,
                    offset=offset,
                )
                self._send_json({"requests": rows, "limit": limit, "offset": offset})
            except (GatewayError, GatewayApiError) as exc:
                self._send_error(exc, HTTPStatus.BAD_REQUEST)
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
            except (GatewayApiError, GatewayError, portal.PortalError, StorageError) as exc:
                self._send_error(exc, HTTPStatus.BAD_REQUEST)
            return
        if path == "/portal/v1/accounts/by_id":
            try:
                _ = self._require_auth()
                account_id = (query.get("account_id") or [""])[0].strip()
                if not account_id:
                    raise GatewayError("account_id required")
                conn = create_connection(_db_path())
                row = conn.execute(
                    "SELECT a.account_id, a.handle, i.public_jwk "
                    "FROM portal_accounts a "
                    "LEFT JOIN e2ee_identities i ON i.account_id = a.account_id "
                    "WHERE a.account_id = ?",
                    (account_id,),
                ).fetchone()
                conn.close()
                if row is None:
                    raise GatewayError("account not found")
                record = {col: row[col] for col in row.keys()}
                public_jwk = record.get("public_jwk")
                if isinstance(public_jwk, str) and public_jwk:
                    try:
                        record["public_jwk"] = json.loads(public_jwk)
                    except Exception:
                        record["public_jwk"] = None
                else:
                    record["public_jwk"] = None
                self._send_json({"account": record})
            except (GatewayApiError, GatewayError, portal.PortalError, StorageError) as exc:
                self._send_error(exc, HTTPStatus.BAD_REQUEST)
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
            except (GatewayApiError, GatewayError, portal.PortalError, StorageError) as exc:
                self._send_error(exc, HTTPStatus.BAD_REQUEST)
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
        if path == "/proof.zip":
            try:
                session = self._require_auth()
                prefix = (query.get("prefix") or [""])[0].strip()
                if not prefix:
                    raise GatewayError("prefix required")
                if len(prefix) > 64 or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", prefix):
                    raise GatewayError("prefix invalid")
                limit_raw = (query.get("limit") or ["200"])[0]
                try:
                    limit = int(limit_raw)
                except ValueError:
                    raise GatewayError("limit invalid")
                if limit < 1 or limit > 500:
                    raise GatewayError("limit out of bounds")

                conn = create_connection(_db_path())
                try:
                    rows = conn.execute(
                        """
                        SELECT DISTINCT r.run_id, r.module, r.action, r.state_hash, r.receipt_hashes, r.replay_ok
                        FROM receipts r
                        WHERE r.run_id LIKE ?
                          AND r.run_id IN (
                            SELECT run_id FROM wallet_transfers WHERE from_address = ? OR to_address = ?
                            UNION
                            SELECT run_id FROM orders WHERE owner_address = ?
                            UNION
                            SELECT run_id FROM listings WHERE publisher_id = ?
                            UNION
                            SELECT run_id FROM purchases WHERE buyer_id = ?
                            UNION
                            SELECT run_id FROM messages WHERE sender_account_id = ?
                          )
                        ORDER BY r.run_id ASC
                        LIMIT ?
                        """,
                        (
                            f"{prefix}%",
                            session.account_id,
                            session.account_id,
                            session.account_id,
                            session.account_id,
                            session.account_id,
                            session.account_id,
                            limit,
                        ),
                    ).fetchall()
                finally:
                    conn.close()

                if not rows:
                    raise GatewayError("no runs found for prefix")

                backend_src = gateway._backend_src()
                if str(backend_src) not in __import__("sys").path:
                    __import__("sys").path.insert(0, str(backend_src))
                from nyx_backend.evidence import EvidenceError, build_export_zip

                manifest_runs = []
                buffer = io.BytesIO()
                with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_STORED) as zip_file:
                    for row in rows:
                        run_id = str(row["run_id"])
                        receipt_hashes_raw = row["receipt_hashes"]
                        receipt_hashes = []
                        if isinstance(receipt_hashes_raw, str) and receipt_hashes_raw:
                            try:
                                receipt_hashes = json.loads(receipt_hashes_raw)
                            except Exception:
                                receipt_hashes = []
                        manifest_runs.append(
                            {
                                "run_id": run_id,
                                "module": str(row["module"]),
                                "action": str(row["action"]),
                                "state_hash": str(row["state_hash"]),
                                "receipt_hashes": receipt_hashes,
                                "replay_ok": bool(row["replay_ok"]),
                            }
                        )
                        try:
                            export_bytes = build_export_zip(run_id, base_dir=_run_root())
                        except EvidenceError as exc:
                            raise GatewayError(f"export failed for {run_id}: {exc}") from exc
                        zip_file.writestr(f"runs/{run_id}.zip", export_bytes)

                    manifest = {
                        "kind": "nyx-proof-package",
                        "version": 1,
                        "account_id": session.account_id,
                        "prefix": prefix,
                        "runs": manifest_runs,
                    }
                    zip_file.writestr(
                        "manifest.json",
                        json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8"),
                    )

                self._send_bytes(buffer.getvalue(), "application/zip")
            except (GatewayApiError, GatewayError, portal.PortalError, StorageError) as exc:
                self._send_error(exc, HTTPStatus.BAD_REQUEST)
            return
        if path == "/list":
            from nyx_backend.evidence import list_runs

            records = list_runs(base_dir=_run_root())
            payload = [{"run_id": record.run_id, "status": record.status} for record in records]
            self._send_json({"runs": payload})
            return
        if path == "/wallet/v1/airdrop/tasks":
            try:
                session = self._require_auth()
                conn = create_connection(_db_path())
                try:
                    tasks = gateway.list_airdrop_tasks_v1(conn, session.account_id)
                finally:
                    conn.close()
                self._send_json({"account_id": session.account_id, "tasks": tasks})
            except (GatewayApiError, GatewayError, portal.PortalError, StorageError) as exc:
                self._send_error(exc, HTTPStatus.BAD_REQUEST)
            return
        if path == "/wallet/v1/balances":
            try:
                session = self._require_auth()
                address = (query.get("address") or [session.account_id])[0]
                if address != session.account_id:
                    raise GatewayApiError(
                        "ADDRESS_MISMATCH",
                        "address must match authenticated account_id",
                        http_status=HTTPStatus.FORBIDDEN,
                    )
                conn = create_connection(_db_path())
                assets = gateway.supported_assets()
                balances = []
                for asset in assets:
                    asset_id = str(asset.get("asset_id", "NYXT"))
                    balances.append({"asset_id": asset_id, "balance": get_wallet_balance(conn, address, asset_id)})
                conn.close()
                self._send_json({"address": address, "assets": assets, "balances": balances})
            except (GatewayApiError, GatewayError, portal.PortalError, StorageError) as exc:
                self._send_error(exc, HTTPStatus.BAD_REQUEST)
            return
        if path == "/wallet/v1/transfers":
            try:
                session = self._require_auth()
                address = (query.get("address") or [session.account_id])[0]
                if address != session.account_id:
                    raise GatewayApiError(
                        "ADDRESS_MISMATCH",
                        "address must match authenticated account_id",
                        http_status=HTTPStatus.FORBIDDEN,
                    )
                limit_raw = (query.get("limit") or ["50"])[0]
                offset_raw = (query.get("offset") or ["0"])[0]
                try:
                    limit = int(limit_raw)
                    offset = int(offset_raw)
                except ValueError:
                    raise GatewayError("limit or offset invalid")
                if limit < 1 or limit > 200:
                    raise GatewayError("limit out of bounds")
                if offset < 0:
                    raise GatewayError("offset out of bounds")
                conn = create_connection(_db_path())
                rows = conn.execute(
                    "SELECT wt.transfer_id, wt.from_address, wt.to_address, wt.asset_id, wt.amount, wt.fee_total, "
                    "wt.treasury_address, wt.run_id, r.state_hash, r.receipt_hashes, r.replay_ok "
                    "FROM wallet_transfers wt "
                    "LEFT JOIN receipts r ON r.run_id = wt.run_id "
                    "WHERE wt.from_address = ? OR wt.to_address = ? "
                    "ORDER BY wt.rowid DESC LIMIT ? OFFSET ?",
                    (address, address, limit, offset),
                ).fetchall()
                transfers = []
                for row in rows:
                    record = {col: row[col] for col in row.keys()}
                    raw_hashes = record.get("receipt_hashes") or "[]"
                    try:
                        record["receipt_hashes"] = json.loads(raw_hashes) if isinstance(raw_hashes, str) else []
                    except Exception:
                        record["receipt_hashes"] = []
                    record["replay_ok"] = bool(record.get("replay_ok"))
                    transfers.append(record)
                conn.close()
                self._send_json({"address": address, "transfers": transfers, "limit": limit, "offset": offset})
            except (GatewayApiError, GatewayError, portal.PortalError, StorageError) as exc:
                self._send_error(exc, HTTPStatus.BAD_REQUEST)
            return
        if path == "/wallet/balance":
            try:
                address = (query.get("address") or [""])[0]
                asset_id = (query.get("asset_id") or ["NYXT"])[0]
                balance = fetch_wallet_balance(address=address, asset_id=asset_id)
                self._send_json({"address": address, "balance": balance})
            except Exception as exc:
                self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        if path == "/exchange/v1/my_orders":
            try:
                session = self._require_auth()
                side = (query.get("side") or [""])[0] or None
                asset_in = (query.get("asset_in") or [""])[0] or None
                asset_out = (query.get("asset_out") or [""])[0] or None
                status = (query.get("status") or ["open"])[0] or "open"
                limit = int((query.get("limit") or ["50"])[0])
                offset = int((query.get("offset") or ["0"])[0])
                if status not in {"open", "filled", "cancelled", "all"}:
                    raise GatewayError("status invalid")
                status_filter = None if status == "all" else status

                conn = create_connection(_db_path())
                clauses = ["o.owner_address = ?"]
                params: list[object] = [session.account_id]
                if side:
                    clauses.append("o.side = ?")
                    params.append(side)
                if asset_in:
                    clauses.append("o.asset_in = ?")
                    params.append(asset_in)
                if asset_out:
                    clauses.append("o.asset_out = ?")
                    params.append(asset_out)
                if status_filter is not None:
                    clauses.append("o.status = ?")
                    params.append(status_filter)
                where = " AND ".join(clauses)
                rows = conn.execute(
                    "SELECT o.order_id, o.owner_address, o.side, o.amount, o.price, o.asset_in, o.asset_out, o.status, o.run_id, "
                    "r.state_hash, r.receipt_hashes, r.replay_ok "
                    "FROM orders o "
                    "LEFT JOIN receipts r ON r.run_id = o.run_id "
                    f"WHERE {where} "
                    "ORDER BY o.rowid DESC LIMIT ? OFFSET ?",
                    (*params, limit, offset),
                ).fetchall()
                orders = []
                for row in rows:
                    record = {col: row[col] for col in row.keys()}
                    raw_hashes = record.get("receipt_hashes") or "[]"
                    try:
                        record["receipt_hashes"] = json.loads(raw_hashes) if isinstance(raw_hashes, str) else []
                    except Exception:
                        record["receipt_hashes"] = []
                    record["replay_ok"] = bool(record.get("replay_ok"))
                    orders.append(record)
                conn.close()
                self._send_json(
                    {"account_id": session.account_id, "orders": orders, "limit": limit, "offset": offset, "status": status}
                )
            except (GatewayApiError, GatewayError, portal.PortalError, StorageError) as exc:
                self._send_error(exc, HTTPStatus.BAD_REQUEST)
            return
        if path == "/exchange/v1/my_trades":
            try:
                session = self._require_auth()
                limit = int((query.get("limit") or ["50"])[0])
                offset = int((query.get("offset") or ["0"])[0])
                conn = create_connection(_db_path())
                rows = conn.execute(
                    "SELECT t.trade_id, t.order_id, t.amount, t.price, t.run_id, "
                    "o.side, o.asset_in, o.asset_out, o.status, "
                    "r.state_hash, r.receipt_hashes, r.replay_ok "
                    "FROM trades t "
                    "JOIN orders o ON o.order_id = t.order_id "
                    "LEFT JOIN receipts r ON r.run_id = t.run_id "
                    "WHERE o.owner_address = ? "
                    "ORDER BY t.trade_id DESC LIMIT ? OFFSET ?",
                    (session.account_id, limit, offset),
                ).fetchall()
                trades = []
                for row in rows:
                    record = {col: row[col] for col in row.keys()}
                    raw_hashes = record.get("receipt_hashes") or "[]"
                    try:
                        record["receipt_hashes"] = json.loads(raw_hashes) if isinstance(raw_hashes, str) else []
                    except Exception:
                        record["receipt_hashes"] = []
                    record["replay_ok"] = bool(record.get("replay_ok"))
                    trades.append(record)
                conn.close()
                self._send_json(
                    {"account_id": session.account_id, "trades": trades, "limit": limit, "offset": offset}
                )
            except (GatewayApiError, GatewayError, portal.PortalError, StorageError) as exc:
                self._send_error(exc, HTTPStatus.BAD_REQUEST)
            return
        if path == "/exchange/orders":
            try:
                conn = create_connection(_db_path())
                side = (query.get("side") or [""])[0] or None
                asset_in = (query.get("asset_in") or [""])[0] or None
                asset_out = (query.get("asset_out") or [""])[0] or None
                status = (query.get("status") or ["open"])[0] or "open"
                limit = int((query.get("limit") or ["100"])[0])
                offset = int((query.get("offset") or ["0"])[0])
                status_filter = None if status == "all" else status
                orders = list_orders(
                    conn,
                    side=side,
                    asset_in=asset_in,
                    asset_out=asset_out,
                    status=status_filter,
                    limit=limit,
                    offset=offset,
                )
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
                limit = int((query.get("limit") or ["50"])[0])
                offset = int((query.get("offset") or ["0"])[0])
                buys = list_orders(conn, side="BUY", order_by="price DESC, order_id ASC", limit=limit, offset=offset)
                sells = list_orders(conn, side="SELL", order_by="price ASC, order_id ASC", limit=limit, offset=offset)
                conn.close()
                self._send_json({"buy": buys, "sell": sells, "limit": limit, "offset": offset})
            except Exception as exc:
                self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        if path == "/chat/messages":
            try:
                session = self._require_auth()
                channel = (query.get("channel") or [""])[0]
                if not channel:
                    raise GatewayError("channel required")
                if channel != "lobby" and session.account_id not in channel:
                    raise GatewayApiError(
                        "FORBIDDEN_CHAT_CHANNEL",
                        "not a channel participant",
                        http_status=403,
                    )
                limit = int((query.get("limit") or ["50"])[0])
                offset = int((query.get("offset") or ["0"])[0])
                if limit < 1 or limit > 200:
                    raise GatewayError("limit out of bounds")
                if offset < 0:
                    raise GatewayError("offset out of bounds")
                conn = create_connection(_db_path())
                rows = conn.execute(
                    "SELECT m.message_id, m.channel, m.sender_account_id, m.body, m.run_id, r.state_hash, r.receipt_hashes, r.replay_ok "
                    "FROM messages m "
                    "LEFT JOIN receipts r ON r.run_id = m.run_id "
                    "WHERE m.channel = ? "
                    "ORDER BY m.rowid DESC LIMIT ? OFFSET ?",
                    (channel, limit, offset),
                ).fetchall()
                messages = []
                for row in rows:
                    record = {col: row[col] for col in row.keys()}
                    raw_hashes = record.get("receipt_hashes") or "[]"
                    try:
                        record["receipt_hashes"] = json.loads(raw_hashes) if isinstance(raw_hashes, str) else []
                    except Exception:
                        record["receipt_hashes"] = []
                    record["replay_ok"] = bool(record.get("replay_ok"))
                    messages.append(record)
                conn.close()
                self._send_json({"channel": channel, "messages": messages, "limit": limit, "offset": offset})
            except (GatewayApiError, GatewayError, portal.PortalError, StorageError) as exc:
                self._send_error(exc, HTTPStatus.BAD_REQUEST)
            return
        if path == "/chat/v1/conversations":
            try:
                session = self._require_auth()
                limit = int((query.get("limit") or ["50"])[0])
                offset = int((query.get("offset") or ["0"])[0])
                if limit < 1 or limit > 200:
                    raise GatewayError("limit out of bounds")
                if offset < 0:
                    raise GatewayError("offset out of bounds")
                conn = create_connection(_db_path())
                rows = conn.execute(
                    "SELECT c.channel, c.max_rowid, m.message_id, m.sender_account_id, m.run_id "
                    "FROM (SELECT channel, MAX(rowid) AS max_rowid FROM messages GROUP BY channel) c "
                    "JOIN messages m ON m.rowid = c.max_rowid "
                    "WHERE c.channel = 'lobby' OR c.channel LIKE ? "
                    "ORDER BY c.max_rowid DESC LIMIT ? OFFSET ?",
                    (f"%{session.account_id}%", limit, offset),
                ).fetchall()
                conversations = []
                for row in rows:
                    conversations.append({col: row[col] for col in row.keys()})
                conn.close()
                self._send_json({"account_id": session.account_id, "conversations": conversations, "limit": limit, "offset": offset})
            except (GatewayApiError, GatewayError, portal.PortalError, StorageError) as exc:
                self._send_error(exc, HTTPStatus.BAD_REQUEST)
            return
        if path == "/integrations/v1/0x/quote":
            try:
                _ = self._require_auth()
                from nyx_backend_gateway.integrations import quote_0x

                network = (query.get("network") or [""])[0].strip() or None
                chain_id_raw = (query.get("chain_id") or [""])[0].strip() or None
                chain_id = int(chain_id_raw) if chain_id_raw else None
                sell_token = (query.get("sell_token") or [""])[0]
                buy_token = (query.get("buy_token") or [""])[0]
                sell_amount = (query.get("sell_amount") or [""])[0].strip() or None
                buy_amount = (query.get("buy_amount") or [""])[0].strip() or None
                taker_address = (query.get("taker_address") or [""])[0].strip() or None
                slippage_bps_raw = (query.get("slippage_bps") or [""])[0].strip() or None
                slippage_bps = int(slippage_bps_raw) if slippage_bps_raw else None

                result = quote_0x(
                    network=network,
                    chain_id=chain_id,
                    sell_token=sell_token,
                    buy_token=buy_token,
                    sell_amount=sell_amount,
                    buy_amount=buy_amount,
                    taker_address=taker_address,
                    slippage_bps=slippage_bps,
                )
                self._send_json(result)
            except (GatewayApiError, GatewayError, portal.PortalError, StorageError, ValueError) as exc:
                self._send_error(exc, HTTPStatus.BAD_REQUEST)
            return
        if path == "/integrations/v1/jupiter/quote":
            try:
                _ = self._require_auth()
                from nyx_backend_gateway.integrations import quote_jupiter

                input_mint = (query.get("input_mint") or [""])[0]
                output_mint = (query.get("output_mint") or [""])[0]
                amount = (query.get("amount") or [""])[0]
                slippage_bps_raw = (query.get("slippage_bps") or [""])[0].strip() or None
                slippage_bps = int(slippage_bps_raw) if slippage_bps_raw else None
                swap_mode = (query.get("swap_mode") or [""])[0].strip() or None

                result = quote_jupiter(
                    input_mint=input_mint,
                    output_mint=output_mint,
                    amount=amount,
                    slippage_bps=slippage_bps,
                    swap_mode=swap_mode,
                )
                self._send_json(result)
            except (GatewayApiError, GatewayError, portal.PortalError, StorageError, ValueError) as exc:
                self._send_error(exc, HTTPStatus.BAD_REQUEST)
            return
        if path == "/integrations/v1/magic_eden/solana/collections":
            try:
                _ = self._require_auth()
                from nyx_backend_gateway.integrations import magic_eden_solana_collections

                limit_raw = (query.get("limit") or [""])[0].strip() or None
                offset_raw = (query.get("offset") or [""])[0].strip() or None
                limit = int(limit_raw) if limit_raw else None
                offset = int(offset_raw) if offset_raw else None

                result = magic_eden_solana_collections(limit=limit, offset=offset)
                self._send_json(result)
            except (GatewayApiError, GatewayError, portal.PortalError, StorageError, ValueError) as exc:
                self._send_error(exc, HTTPStatus.BAD_REQUEST)
            return
        if path == "/integrations/v1/magic_eden/solana/collection_listings":
            try:
                _ = self._require_auth()
                from nyx_backend_gateway.integrations import magic_eden_solana_collection_listings

                symbol = (query.get("symbol") or [""])[0]
                limit_raw = (query.get("limit") or [""])[0].strip() or None
                offset_raw = (query.get("offset") or [""])[0].strip() or None
                limit = int(limit_raw) if limit_raw else None
                offset = int(offset_raw) if offset_raw else None

                result = magic_eden_solana_collection_listings(symbol=symbol, limit=limit, offset=offset)
                self._send_json(result)
            except (GatewayApiError, GatewayError, portal.PortalError, StorageError, ValueError) as exc:
                self._send_error(exc, HTTPStatus.BAD_REQUEST)
            return
        if path == "/integrations/v1/magic_eden/solana/token":
            try:
                _ = self._require_auth()
                from nyx_backend_gateway.integrations import magic_eden_solana_token

                mint = (query.get("mint") or [""])[0]
                result = magic_eden_solana_token(mint=mint)
                self._send_json(result)
            except (GatewayApiError, GatewayError, portal.PortalError, StorageError, ValueError) as exc:
                self._send_error(exc, HTTPStatus.BAD_REQUEST)
            return
        if path == "/integrations/v1/magic_eden/evm/collections/search":
            try:
                _ = self._require_auth()
                from nyx_backend_gateway.integrations import magic_eden_evm_search_collections

                chain = (query.get("chain") or [""])[0]
                pattern = (query.get("pattern") or [""])[0]
                limit_raw = (query.get("limit") or [""])[0].strip() or None
                offset_raw = (query.get("offset") or [""])[0].strip() or None
                limit = int(limit_raw) if limit_raw else None
                offset = int(offset_raw) if offset_raw else None

                result = magic_eden_evm_search_collections(chain=chain, pattern=pattern, limit=limit, offset=offset)
                self._send_json(result)
            except (GatewayApiError, GatewayError, portal.PortalError, StorageError, ValueError) as exc:
                self._send_error(exc, HTTPStatus.BAD_REQUEST)
            return
        if path == "/integrations/v1/magic_eden/evm/collections":
            try:
                _ = self._require_auth()
                from nyx_backend_gateway.integrations import magic_eden_evm_collections, _split_csv

                chain = (query.get("chain") or [""])[0]
                slugs_raw = (query.get("collection_slugs") or [""])[0]
                ids_raw = (query.get("collection_ids") or [""])[0]
                slugs = _split_csv(slugs_raw, name="collection_slugs", max_items=50)
                ids = _split_csv(ids_raw, name="collection_ids", max_items=50)

                result = magic_eden_evm_collections(chain=chain, collection_slugs=slugs, collection_ids=ids)
                self._send_json(result)
            except (GatewayApiError, GatewayError, portal.PortalError, StorageError, ValueError) as exc:
                self._send_error(exc, HTTPStatus.BAD_REQUEST)
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
        if path == "/portal/v1/accounts/search":
            try:
                _ = self._require_auth()
                q = (query.get("q") or [""])[0].strip()
                if not q:
                    raise GatewayError("q required")
                limit = int((query.get("limit") or ["20"])[0])
                if limit < 1 or limit > 50:
                    raise GatewayError("limit out of bounds")
                conn = create_connection(_db_path())
                rows = conn.execute(
                    "SELECT a.account_id, a.handle, i.public_jwk "
                    "FROM portal_accounts a "
                    "LEFT JOIN e2ee_identities i ON i.account_id = a.account_id "
                    "WHERE a.handle LIKE ? "
                    "ORDER BY a.handle ASC LIMIT ?",
                    (f"{q}%", limit),
                ).fetchall()
                accounts = []
                for row in rows:
                    record = {col: row[col] for col in row.keys()}
                    public_jwk = record.get("public_jwk")
                    if isinstance(public_jwk, str) and public_jwk:
                        try:
                            record["public_jwk"] = json.loads(public_jwk)
                        except Exception:
                            record["public_jwk"] = None
                    else:
                        record["public_jwk"] = None
                    accounts.append(record)
                conn.close()
                self._send_json({"accounts": accounts, "q": q, "limit": limit})
            except (GatewayApiError, GatewayError, portal.PortalError, StorageError) as exc:
                self._send_error(exc, HTTPStatus.BAD_REQUEST)
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
                limit = int((query.get("limit") or ["50"])[0])
                offset = int((query.get("offset") or ["0"])[0])
                conn = create_connection(_db_path())
                listings = gateway.marketplace_list_active_listings(conn, limit=limit, offset=offset)
                conn.close()
                self._send_json({"listings": listings, "limit": limit, "offset": offset})
            except (GatewayApiError, GatewayError, portal.PortalError, StorageError) as exc:
                self._send_error(exc, HTTPStatus.BAD_REQUEST)
            return
        if path == "/marketplace/listings/search":
            try:
                q = (query.get("q") or [""])[0]
                limit = int((query.get("limit") or ["50"])[0])
                offset = int((query.get("offset") or ["0"])[0])
                conn = create_connection(_db_path())
                listings = gateway.marketplace_search_listings(conn, q, limit=limit, offset=offset)
                conn.close()
                self._send_json({"listings": listings, "limit": limit, "offset": offset, "q": q})
            except (GatewayApiError, GatewayError, portal.PortalError, StorageError) as exc:
                self._send_error(exc, HTTPStatus.BAD_REQUEST)
            return
        if path == "/marketplace/v1/my_purchases":
            try:
                session = self._require_auth()
                limit = int((query.get("limit") or ["50"])[0])
                offset = int((query.get("offset") or ["0"])[0])
                if limit < 1 or limit > 200:
                    raise GatewayError("limit out of bounds")
                if offset < 0:
                    raise GatewayError("offset out of bounds")
                conn = create_connection(_db_path())
                rows = conn.execute(
                    "SELECT p.purchase_id, p.listing_id, p.buyer_id, p.qty, p.run_id, "
                    "l.publisher_id, l.sku, l.title, l.price, l.status, "
                    "r.state_hash, r.receipt_hashes, r.replay_ok "
                    "FROM purchases p "
                    "LEFT JOIN listings l ON l.listing_id = p.listing_id "
                    "LEFT JOIN receipts r ON r.run_id = p.run_id "
                    "WHERE p.buyer_id = ? "
                    "ORDER BY p.rowid DESC LIMIT ? OFFSET ?",
                    (session.account_id, limit, offset),
                ).fetchall()
                purchases = []
                for row in rows:
                    record = {col: row[col] for col in row.keys()}
                    raw_hashes = record.get("receipt_hashes") or "[]"
                    try:
                        record["receipt_hashes"] = json.loads(raw_hashes) if isinstance(raw_hashes, str) else []
                    except Exception:
                        record["receipt_hashes"] = []
                    record["replay_ok"] = bool(record.get("replay_ok"))
                    purchases.append(record)
                conn.close()
                self._send_json({"account_id": session.account_id, "purchases": purchases, "limit": limit, "offset": offset})
            except (GatewayApiError, GatewayError, portal.PortalError, StorageError) as exc:
                self._send_error(exc, HTTPStatus.BAD_REQUEST)
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
