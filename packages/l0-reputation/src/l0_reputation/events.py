from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from l0_reputation.errors import ValidationError
from l0_reputation.hashing import compare_digest, ensure_bytes32, framed, sha256


class RepEventKind(Enum):
    EARN = "EARN"
    SPEND = "SPEND"
    SLASH = "SLASH"


@dataclass(frozen=True)
class RepEvent:
    context_id: bytes
    pseudonym_id: bytes
    kind: RepEventKind
    amount: int
    nonce: bytes
    event_id: bytes

    def __post_init__(self) -> None:
        object.__setattr__(self, "context_id", ensure_bytes32(self.context_id, "context_id"))
        object.__setattr__(self, "pseudonym_id", ensure_bytes32(self.pseudonym_id, "pseudonym_id"))
        if not isinstance(self.kind, RepEventKind):
            raise ValidationError("kind must be RepEventKind")
        if not isinstance(self.amount, int) or isinstance(self.amount, bool):
            raise ValidationError("amount must be int")
        if self.amount <= 0:
            raise ValidationError("amount must be > 0")
        object.__setattr__(self, "nonce", ensure_bytes32(self.nonce, "nonce"))
        object.__setattr__(self, "event_id", ensure_bytes32(self.event_id, "event_id"))
        expected = compute_event_id(
            self.context_id,
            self.pseudonym_id,
            self.kind,
            self.amount,
            self.nonce,
        )
        if not compare_digest(self.event_id, expected):
            raise ValidationError("event_id mismatch")


def compute_event_id(
    context_id: bytes,
    pseudonym_id: bytes,
    kind: RepEventKind,
    amount: int,
    nonce: bytes,
) -> bytes:
    context = ensure_bytes32(context_id, "context_id")
    pseudo = ensure_bytes32(pseudonym_id, "pseudonym_id")
    if not isinstance(kind, RepEventKind):
        raise ValidationError("kind must be RepEventKind")
    if not isinstance(amount, int) or isinstance(amount, bool):
        raise ValidationError("amount must be int")
    if amount <= 0:
        raise ValidationError("amount must be > 0")
    nonce_bytes = ensure_bytes32(nonce, "nonce")
    amount_bytes = str(amount).encode("ascii")
    kind_bytes = kind.value.encode("utf-8")
    event_id = sha256(
        framed(
            [
                b"NYX:REP:EVENT:v1",
                context,
                pseudo,
                kind_bytes,
                amount_bytes,
                nonce_bytes,
            ]
        )
    )
    return ensure_bytes32(event_id, "event_id")
