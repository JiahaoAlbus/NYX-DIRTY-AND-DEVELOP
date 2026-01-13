from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass

from l2_private_ledger.errors import ValidationError


def ensure_bytes32(value: object, name: str) -> bytes:
    if isinstance(value, Bytes32):
        value = value.value
    if not isinstance(value, (bytes, bytearray)):
        raise ValidationError(f"{name} must be bytes32")
    if isinstance(value, bytearray):
        value = bytes(value)
    if len(value) != 32:
        raise ValidationError(f"{name} must be 32 bytes")
    return value


def compare_digest(a: bytes, b: bytes) -> bool:
    return hmac.compare_digest(a, b)


def sha256(data: bytes) -> bytes:
    if not isinstance(data, (bytes, bytearray)):
        raise ValidationError("sha256 input must be bytes")
    return hashlib.sha256(bytes(data)).digest()


def framed(parts: list[bytes]) -> bytes:
    payload = bytearray()
    for part in parts:
        if not isinstance(part, (bytes, bytearray)):
            raise ValidationError("framed parts must be bytes")
        part_bytes = bytes(part)
        payload.extend(len(part_bytes).to_bytes(4, "big"))
        payload.extend(part_bytes)
    return bytes(payload)


def xor_one_bit(value: bytes, bit_index: int) -> bytes:
    data = bytearray(ensure_bytes32(value, "xor_one_bit"))
    if not isinstance(bit_index, int) or isinstance(bit_index, bool):
        raise ValidationError("bit_index must be int")
    if bit_index < 0 or bit_index >= 256:
        raise ValidationError("bit_index out of range")
    byte_index = bit_index // 8
    bit = 1 << (bit_index % 8)
    data[byte_index] ^= bit
    return bytes(data)


@dataclass(frozen=True)
class Bytes32:
    value: bytes

    def __post_init__(self) -> None:
        ensure_bytes32(self.value, "bytes32")

    def hex(self) -> str:
        return self.value.hex()


@dataclass(frozen=True)
class Commitment:
    value: Bytes32


@dataclass(frozen=True)
class Nullifier:
    value: Bytes32


@dataclass(frozen=True)
class LedgerRoot:
    value: Bytes32


@dataclass(frozen=True)
class Note:
    note_id: Bytes32
    commitment: Commitment
    value: int
    memo: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.value, int) or isinstance(self.value, bool):
            raise ValidationError("note value must be int")
        if self.memo is not None and not isinstance(self.memo, str):
            raise ValidationError("memo must be string or None")
