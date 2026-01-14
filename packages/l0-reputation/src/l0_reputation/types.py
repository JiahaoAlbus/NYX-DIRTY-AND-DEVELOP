from __future__ import annotations

from dataclasses import dataclass

from l0_reputation.errors import ValidationError
from l0_reputation.hashing import ensure_bytes32


@dataclass(frozen=True)
class Bytes32:
    value: bytes

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", ensure_bytes32(self.value, "bytes32"))

    def hex(self) -> str:
        return self.value.hex()


@dataclass(frozen=True)
class PseudonymId:
    value: Bytes32


@dataclass(frozen=True)
class RepRoot:
    value: Bytes32


@dataclass(frozen=True)
class RepEventId:
    value: Bytes32
