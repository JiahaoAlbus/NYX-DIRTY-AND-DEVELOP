from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from l1_chain.types import (
    ChainAccount,
    ChainId,
    TxEnvelope,
    TxSignature,
    build_tx_envelope,
)

from wallet_kernel.canonical import (
    CanonicalizationError,
    require_bytes32,
    require_text,
    sha256,
)
from wallet_kernel.errors import ValidationError
from wallet_kernel.keystore import KeyStore
from wallet_kernel.secrets import SecretBytes
from wallet_kernel.signing import Signer


class NonceSource(ABC):
    @abstractmethod
    def next_nonce(self) -> bytes:
        raise NotImplementedError


class InMemoryNonceSource(NonceSource):
    def __init__(self, salt: bytes | None = None) -> None:
        if salt is None:
            salt = b"wallet-kernel-nonce"
        if not isinstance(salt, bytes):
            raise ValidationError("salt must be bytes")
        self._salt = salt
        self._counter = 0

    def next_nonce(self) -> bytes:
        counter_bytes = self._counter.to_bytes(8, "big")
        self._counter += 1
        return sha256(self._salt + counter_bytes)


@dataclass(frozen=True)
class TxBuilder:
    keystore: KeyStore
    signer: Signer
    nonce_source: NonceSource

    def __post_init__(self) -> None:
        if not isinstance(self.keystore, KeyStore):
            raise ValidationError("keystore must be KeyStore")
        if not isinstance(self.signer, Signer):
            raise ValidationError("signer must be Signer")
        if not isinstance(self.nonce_source, NonceSource):
            raise ValidationError("nonce_source must be NonceSource")

    def build_and_sign_tx(
        self,
        *,
        chain_id: ChainId,
        sender: ChainAccount,
        key_id: str,
        payload: bytes,
    ) -> TxEnvelope:
        if not isinstance(chain_id, ChainId):
            raise ValidationError("chain_id must be ChainId")
        if not isinstance(sender, ChainAccount):
            raise ValidationError("sender must be ChainAccount")
        if not isinstance(payload, bytes):
            raise ValidationError("payload must be bytes")
        key = require_text(key_id, "key_id")
        secret = self.keystore.get_key(key)
        if not isinstance(secret, SecretBytes):
            raise ValidationError("secret must be SecretBytes")
        nonce = self.nonce_source.next_nonce()
        try:
            require_bytes32(nonce, "nonce")
        except CanonicalizationError as exc:
            raise ValidationError(str(exc)) from exc
        signature_bytes = self.signer.sign(payload, secret)
        signature = TxSignature(signature_bytes)
        return build_tx_envelope(
            chain_id=chain_id,
            sender=sender,
            nonce=nonce,
            payload=payload,
            signature=signature,
        )
