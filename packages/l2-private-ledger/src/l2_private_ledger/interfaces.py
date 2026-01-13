from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol

from l2_private_ledger.types import Commitment, LedgerRoot, Note, Nullifier, Bytes32


class PrivateLedgerKernel(ABC):
    @abstractmethod
    def create_note(self, note: Note) -> Commitment:
        raise NotImplementedError

    @abstractmethod
    def spend(self, nullifier: Nullifier, ledger_root: LedgerRoot, context_id: Bytes32) -> None:
        raise NotImplementedError

    @abstractmethod
    def root(self) -> LedgerRoot:
        raise NotImplementedError


class NoteStore(Protocol):
    def put(self, note: Note) -> None:
        raise NotImplementedError

    def get(self, commitment: Commitment) -> Note | None:
        raise NotImplementedError


class NullifierStore(Protocol):
    def mark_spent(self, nullifier: Nullifier) -> None:
        raise NotImplementedError

    def is_spent(self, nullifier: Nullifier) -> bool:
        raise NotImplementedError
