from __future__ import annotations

import hashlib
import hmac

from l0_reputation.errors import ValidationError

HASH_BYTES = 32


def ensure_bytes32(value: object, name: str) -> bytes:
    if not isinstance(value, (bytes, bytearray)):
        raise ValidationError(f"{name} must be 32 bytes")
    raw = bytes(value)
    if len(raw) != HASH_BYTES:
        raise ValidationError(f"{name} must be 32 bytes")
    return raw


def compare_digest(left: bytes, right: bytes) -> bool:
    return hmac.compare_digest(left, right)


def sha256(data: bytes) -> bytes:
    if not isinstance(data, bytes):
        raise ValidationError("data must be bytes")
    return hashlib.sha256(data).digest()


def framed(parts: list[bytes]) -> bytes:
    payload = bytearray()
    for part in parts:
        if not isinstance(part, (bytes, bytearray)):
            raise ValidationError("framed parts must be bytes")
        part_bytes = bytes(part)
        payload.extend(len(part_bytes).to_bytes(4, "big"))
        payload.extend(part_bytes)
    return bytes(payload)


def bytes32_hex(value: object, name: str) -> str:
    return ensure_bytes32(value, name).hex()


def hex_to_bytes32(value: object, name: str) -> bytes:
    if not isinstance(value, str):
        raise ValidationError(f"{name} must be hex string")
    if len(value) != 64:
        raise ValidationError(f"{name} must be 32-byte hex")
    try:
        raw = bytes.fromhex(value)
    except ValueError as exc:
        raise ValidationError(f"{name} must be hex") from exc
    return ensure_bytes32(raw, name)
