from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from l2_private_ledger.errors import ValidationError
from l2_private_ledger.types import Bytes32, ensure_bytes32


class ActionKind(Enum):
    PRIVATE_MINT = "PRIVATE_MINT"
    PRIVATE_SPEND = "PRIVATE_SPEND"


@dataclass(frozen=True)
class PrivateMint:
    commitment: bytes

    def __post_init__(self) -> None:
        object.__setattr__(self, "commitment", ensure_bytes32(self.commitment, "commitment"))


@dataclass(frozen=True)
class PrivateSpend:
    nullifier: bytes

    def __post_init__(self) -> None:
        object.__setattr__(self, "nullifier", ensure_bytes32(self.nullifier, "nullifier"))


@dataclass(frozen=True)
class LedgerAction:
    kind: ActionKind
    payload: PrivateMint | PrivateSpend

    def __post_init__(self) -> None:
        if not isinstance(self.kind, ActionKind):
            raise ValidationError("invalid action kind")
        if self.kind == ActionKind.PRIVATE_MINT and not isinstance(self.payload, PrivateMint):
            raise ValidationError("payload must be PrivateMint")
        if self.kind == ActionKind.PRIVATE_SPEND and not isinstance(self.payload, PrivateSpend):
            raise ValidationError("payload must be PrivateSpend")
