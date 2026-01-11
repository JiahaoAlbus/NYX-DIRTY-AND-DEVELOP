from __future__ import annotations

import hashlib
import hmac

HASH_BYTES = 32


class HashingError(ValueError):
    pass


def sha256(data: bytes) -> bytes:
    if not isinstance(data, bytes):
        raise HashingError("data must be bytes")
    return hashlib.sha256(data).digest()


def compare_digest(left: bytes, right: bytes) -> bool:
    return hmac.compare_digest(left, right)


def require_bytes32(value: object, field_name: str) -> bytes:
    if not isinstance(value, bytes):
        raise HashingError(f"{field_name} must be bytes")
    if len(value) != HASH_BYTES:
        raise HashingError(f"{field_name} must be 32 bytes")
    return value


def bytes32_hex(value: bytes, field_name: str) -> str:
    return require_bytes32(value, field_name).hex()


def hex_to_bytes32(value: str, field_name: str) -> bytes:
    if not isinstance(value, str):
        raise HashingError(f"{field_name} must be hex string")
    if len(value) != HASH_BYTES * 2:
        raise HashingError(f"{field_name} must be 64 hex chars")
    try:
        data = bytes.fromhex(value)
    except ValueError as exc:
        raise HashingError(f"{field_name} must be hex") from exc
    return require_bytes32(data, field_name)
