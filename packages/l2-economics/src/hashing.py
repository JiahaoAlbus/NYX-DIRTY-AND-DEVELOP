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
        raise HashingError(f"{field_name} must be 32 bytes")
    if len(value) != HASH_BYTES:
        raise HashingError(f"{field_name} must be 32 bytes")
    return value


def bytes32_hex(value: object, field_name: str) -> str:
    data = require_bytes32(value, field_name)
    return data.hex()


def encode_len_prefixed(text: str, field_name: str) -> bytes:
    if not isinstance(text, str):
        raise HashingError(f"{field_name} must be a string")
    data = text.encode("utf-8")
    if len(data) > 0xFFFFFFFF:
        raise HashingError("text field too large")
    return len(data).to_bytes(4, "big") + data


def encode_len_prefixed_bytes(data: bytes, field_name: str) -> bytes:
    if not isinstance(data, bytes):
        raise HashingError(f"{field_name} must be bytes")
    if len(data) > 0xFFFFFFFF:
        raise HashingError("byte field too large")
    return len(data).to_bytes(4, "big") + data
