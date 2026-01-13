from __future__ import annotations

from dataclasses import dataclass


class LedgerTypeError(ValueError):
    pass


@dataclass(frozen=True)
class Bytes32:
    value: bytes

    def __post_init__(self) -> None:
        if not isinstance(self.value, (bytes, bytearray)):
            raise LedgerTypeError("bytes32 must be bytes")
        if isinstance(self.value, bytearray):
            object.__setattr__(self, "value", bytes(self.value))
        if len(self.value) != 32:
            raise LedgerTypeError("bytes32 must be 32 bytes")

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
            raise LedgerTypeError("note value must be int")
        if self.memo is not None and not isinstance(self.memo, str):
            raise LedgerTypeError("memo must be string or None")
