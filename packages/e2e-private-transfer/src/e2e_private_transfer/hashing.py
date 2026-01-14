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


def require_bytes32(value: object, name: str) -> bytes:
    if not isinstance(value, bytes):
        raise HashingError(f"{name} must be 32 bytes")
    if len(value) != HASH_BYTES:
        raise HashingError(f"{name} must be 32 bytes")
    return value


def bytes32_hex(value: object, name: str) -> str:
    return require_bytes32(value, name).hex()


def hex_to_bytes32(value: object, name: str) -> bytes:
    if not isinstance(value, str):
        raise HashingError(f"{name} must be hex string")
    if len(value) != 64:
        raise HashingError(f"{name} must be 32-byte hex")
    try:
        raw = bytes.fromhex(value)
    except ValueError as exc:
        raise HashingError(f"{name} must be hex") from exc
    return require_bytes32(raw, name)


def framed(parts: list[bytes]) -> bytes:
    payload = bytearray()
    for part in parts:
        if not isinstance(part, (bytes, bytearray)):
            raise HashingError("framed parts must be bytes")
        part_bytes = bytes(part)
        payload.extend(len(part_bytes).to_bytes(4, "big"))
        payload.extend(part_bytes)
    return bytes(payload)


def xor_one_bit(value: bytes, bit_index: int) -> bytes:
    data = bytearray(require_bytes32(value, "xor_one_bit"))
    if not isinstance(bit_index, int) or isinstance(bit_index, bool):
        raise HashingError("bit_index must be int")
    if bit_index < 0 or bit_index >= 256:
        raise HashingError("bit_index out of range")
    byte_index = bit_index // 8
    bit = 1 << (bit_index % 8)
    data[byte_index] ^= bit
    return bytes(data)
