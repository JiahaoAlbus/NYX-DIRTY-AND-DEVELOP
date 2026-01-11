from __future__ import annotations

import hashlib
import hmac
from abc import ABC, abstractmethod

from wallet_kernel.canonical import compare_digest
from wallet_kernel.errors import SigningError
from wallet_kernel.secrets import SecretBytes


class Signer(ABC):
    @abstractmethod
    def sign(self, message: bytes, secret: SecretBytes) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def verify(self, message: bytes, signature: bytes, secret: SecretBytes) -> bool:
        raise NotImplementedError


class HMACSigner(Signer):
    def sign(self, message: bytes, secret: SecretBytes) -> bytes:
        if not isinstance(message, bytes):
            raise SigningError("message must be bytes")
        if not isinstance(secret, SecretBytes):
            raise SigningError("secret must be SecretBytes")
        return hmac.new(secret._raw(), message, hashlib.sha256).digest()

    def verify(self, message: bytes, signature: bytes, secret: SecretBytes) -> bool:
        if not isinstance(signature, bytes):
            raise SigningError("signature must be bytes")
        expected = self.sign(message, secret)
        return compare_digest(expected, signature)
