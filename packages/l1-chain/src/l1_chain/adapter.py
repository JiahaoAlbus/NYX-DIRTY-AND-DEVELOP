from __future__ import annotations

from abc import ABC, abstractmethod

from l1_chain.types import FinalityProof, StateProof, TxEnvelope, TxHash, StateRoot


class ChainAdapter(ABC):
    @abstractmethod
    def submit_tx(self, tx: TxEnvelope) -> TxHash:
        raise NotImplementedError

    @abstractmethod
    def get_finality(self, tx_hash: TxHash) -> FinalityProof | None:
        raise NotImplementedError

    @abstractmethod
    def read_state(self, key: bytes) -> tuple[bytes | None, StateRoot]:
        raise NotImplementedError

    @abstractmethod
    def verify_state_proof(self, proof: StateProof) -> bool:
        raise NotImplementedError
