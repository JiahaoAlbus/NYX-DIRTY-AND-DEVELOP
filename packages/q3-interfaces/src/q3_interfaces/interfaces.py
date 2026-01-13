from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol

from q3_interfaces.types import Bytes32, TraceRef


class ProofProvider(ABC):
    @abstractmethod
    def prove(
        self,
        statement_id: str,
        context_id: Bytes32,
        nonce: Bytes32,
        public_inputs: dict,
        witness: dict,
    ) -> bytes:
        raise NotImplementedError


class ProofVerifier(ABC):
    @abstractmethod
    def verify(
        self,
        envelope: object,
        expected_context: Bytes32,
        expected_statement: str,
    ) -> bool:
        raise NotImplementedError


class FeePolicyHook(ABC):
    @abstractmethod
    def evaluate(self, action: dict, fee_total: int) -> bool:
        raise NotImplementedError


class ChainFinalityProvider(ABC):
    @abstractmethod
    def get_finality(self, tx_hash: Bytes32) -> object | None:
        raise NotImplementedError


class ReceiptVerifier(ABC):
    @abstractmethod
    def verify(self, receipt: object, trace_ref: TraceRef) -> bool:
        raise NotImplementedError


class TraceStore(Protocol):
    def store(self, trace_ref: TraceRef, payload: str) -> None:
        ...
