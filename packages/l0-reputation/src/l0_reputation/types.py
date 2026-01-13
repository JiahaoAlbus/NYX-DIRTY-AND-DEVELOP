from __future__ import annotations

from dataclasses import dataclass


class ReputationTypeError(ValueError):
    pass


@dataclass(frozen=True)
class Bytes32:
    value: bytes

    def __post_init__(self) -> None:
        if not isinstance(self.value, (bytes, bytearray)):
            raise ReputationTypeError("bytes32 must be bytes")
        if isinstance(self.value, bytearray):
            object.__setattr__(self, "value", bytes(self.value))
        if len(self.value) != 32:
            raise ReputationTypeError("bytes32 must be 32 bytes")

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


@dataclass(frozen=True)
class RepEvent:
    event_id: RepEventId
    context_id: Bytes32
    payload: dict

    def __post_init__(self) -> None:
        if not isinstance(self.payload, dict):
            raise ReputationTypeError("payload must be dict")
