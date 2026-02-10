from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass


class AuthError(ValueError):
    pass


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def generate_session_id() -> str:
    return secrets.token_hex(16)


def issue_token(
    *,
    account_id: str,
    session_id: str,
    expires_at: int,
    secret: str,
) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": account_id,
        "sid": session_id,
        "exp": expires_at,
        "iat": int(time.time()),
        "ver": 1,
    }
    header_b64 = _b64url(json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    payload_b64 = _b64url(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    signature = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    sig_b64 = _b64url(signature)
    return f"{header_b64}.{payload_b64}.{sig_b64}"


@dataclass(frozen=True)
class TokenPayload:
    account_id: str
    session_id: str
    expires_at: int


def verify_token(token: str, secret: str) -> TokenPayload:
    parts = token.split(".")
    if len(parts) != 3:
        raise AuthError("token invalid")
    header_b64, payload_b64, sig_b64 = parts
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    expected = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    provided = _b64url_decode(sig_b64)
    if not hmac.compare_digest(expected, provided):
        raise AuthError("token signature invalid")
    try:
        payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
    except Exception as exc:
        raise AuthError("token payload invalid") from exc
    account_id = payload.get("sub")
    session_id = payload.get("sid")
    expires_at = payload.get("exp")
    if not isinstance(account_id, str) or not account_id:
        raise AuthError("token subject invalid")
    if not isinstance(session_id, str) or not session_id:
        raise AuthError("token session invalid")
    if not isinstance(expires_at, int):
        raise AuthError("token expiry invalid")
    if int(time.time()) > expires_at:
        raise AuthError("token expired")
    return TokenPayload(account_id=account_id, session_id=session_id, expires_at=expires_at)
