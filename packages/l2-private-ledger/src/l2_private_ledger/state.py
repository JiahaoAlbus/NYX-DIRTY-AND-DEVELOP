from __future__ import annotations

from dataclasses import dataclass

from l2_private_ledger.errors import ValidationError
from l2_private_ledger.types import framed, sha256, ensure_bytes32


@dataclass(frozen=True)
class LedgerState:
    commitments: frozenset[bytes]
    nullifiers: frozenset[bytes]

    def __post_init__(self) -> None:
        for value in self.commitments:
            ensure_bytes32(value, "commitment")
        for value in self.nullifiers:
            ensure_bytes32(value, "nullifier")


def empty_state() -> LedgerState:
    return LedgerState(commitments=frozenset(), nullifiers=frozenset())


def _sorted_bytes(values: frozenset[bytes]) -> list[bytes]:
    return sorted(values)


def recompute_root(state: LedgerState) -> bytes:
    commitments = _sorted_bytes(state.commitments)
    nullifiers = _sorted_bytes(state.nullifiers)
    commitments_hash = sha256(framed([b"NYX:PL:C:v0", *commitments]))
    nullifiers_hash = sha256(framed([b"NYX:PL:N:v0", *nullifiers]))
    return sha256(framed([b"NYX:PL:ROOT:v0", commitments_hash, nullifiers_hash]))


def state_root(state: LedgerState) -> bytes:
    root = recompute_root(state)
    ensure_bytes32(root, "state_root")
    return root
