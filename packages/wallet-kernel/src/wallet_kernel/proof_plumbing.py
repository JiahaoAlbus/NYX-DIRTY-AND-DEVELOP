from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from wallet_kernel.canonical import require_bytes32, require_text
from wallet_kernel.errors import ProofError

try:
    from envelope import ProofEnvelope
    from verifier import ProofAdapter, verify as verify_proof
except ImportError as exc:  # pragma: no cover - handled at runtime
    ProofEnvelope = None  # type: ignore
    ProofAdapter = object  # type: ignore
    _IMPORT_ERROR = exc

    def verify_proof(*args, **kwargs):
        raise ProofError("l0-zk-id verify unavailable") from _IMPORT_ERROR


@dataclass(frozen=True)
class ProofBundle:
    payload: bytes
    proofs: tuple[ProofEnvelope, ...]

    def __post_init__(self) -> None:
        if ProofEnvelope is None:
            raise ProofError("l0-zk-id verify unavailable")
        if not isinstance(self.payload, bytes):
            raise ProofError("payload must be bytes")
        if not isinstance(self.proofs, tuple):
            raise ProofError("proofs must be a tuple")
        for envelope in self.proofs:
            if not isinstance(envelope, ProofEnvelope):
                raise ProofError("proof must be ProofEnvelope")


class ProofCarrier:
    @staticmethod
    def attach(payload: bytes, proofs: Iterable[ProofEnvelope] | None) -> ProofBundle:
        if proofs is None:
            proof_list: tuple[ProofEnvelope, ...] = ()
        else:
            proof_list = tuple(proofs)
        return ProofBundle(payload=payload, proofs=proof_list)


class ProofVerifier:
    def __init__(self, adapter: ProofAdapter) -> None:
        if ProofEnvelope is None:
            raise ProofError("l0-zk-id verify unavailable")
        if adapter is None or not hasattr(adapter, "verify"):
            raise ProofError("adapter must provide verify")
        self._adapter = adapter

    def verify_all(
        self,
        proofs: Iterable[ProofEnvelope],
        expected_context_id: bytes,
        expected_statement_id: str,
    ) -> bool:
        require_bytes32(expected_context_id, "expected_context_id")
        require_text(expected_statement_id, "expected_statement_id")
        for envelope in proofs:
            if not verify_proof(
                envelope,
                expected_context_id,
                expected_statement_id,
                self._adapter,
            ):
                return False
        return True
