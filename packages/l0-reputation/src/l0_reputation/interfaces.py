from __future__ import annotations

from abc import ABC, abstractmethod

from l0_reputation.types import Bytes32, PseudonymId, RepEvent, RepRoot


class DisclosureStatement(ABC):
    @abstractmethod
    def context_id(self) -> Bytes32:
        raise NotImplementedError

    @abstractmethod
    def statement_id(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def payload(self) -> dict:
        raise NotImplementedError


class ReputationKernel(ABC):
    @abstractmethod
    def record_event(self, context_id: Bytes32, event: RepEvent) -> RepRoot:
        raise NotImplementedError

    @abstractmethod
    def root(self, pseudonym: PseudonymId) -> RepRoot:
        raise NotImplementedError

    @abstractmethod
    def verify_disclosure(self, context_id: Bytes32, statement: DisclosureStatement) -> bool:
        raise NotImplementedError
