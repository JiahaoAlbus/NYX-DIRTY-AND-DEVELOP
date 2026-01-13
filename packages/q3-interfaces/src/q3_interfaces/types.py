from __future__ import annotations

from dataclasses import dataclass


class Q3TypeError(ValueError):
    pass


@dataclass(frozen=True)
class Bytes32:
    value: bytes

    def __post_init__(self) -> None:
        if not isinstance(self.value, (bytes, bytearray)):
            raise Q3TypeError("bytes32 must be bytes")
        if isinstance(self.value, bytearray):
            object.__setattr__(self, "value", bytes(self.value))
        if len(self.value) != 32:
            raise Q3TypeError("bytes32 must be 32 bytes")

    def hex(self) -> str:
        return self.value.hex()

    @classmethod
    def from_hex(cls, raw: str) -> "Bytes32":
        if not isinstance(raw, str):
            raise Q3TypeError("hex must be str")
        try:
            data = bytes.fromhex(raw)
        except ValueError as exc:
            raise Q3TypeError("hex is invalid") from exc
        return cls(data)


@dataclass(frozen=True)
class HexStr:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not self.value:
            raise Q3TypeError("hex string required")
        try:
            bytes.fromhex(self.value)
        except ValueError as exc:
            raise Q3TypeError("hex string invalid") from exc


@dataclass(frozen=True)
class TraceRef:
    trace_hash: Bytes32
    label: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.label, str):
            raise Q3TypeError("label must be string")
