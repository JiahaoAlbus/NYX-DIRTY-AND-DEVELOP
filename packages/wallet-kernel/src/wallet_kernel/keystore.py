from __future__ import annotations

from abc import ABC, abstractmethod

from wallet_kernel.canonical import require_text
from wallet_kernel.errors import KeyStoreError
from wallet_kernel.secrets import SecretBytes


class KeyStore(ABC):
    @abstractmethod
    def put_key(self, key_id: str, secret: SecretBytes) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_key(self, key_id: str) -> SecretBytes:
        raise NotImplementedError

    @abstractmethod
    def delete_key(self, key_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_keys(self) -> list[str]:
        raise NotImplementedError


class InMemoryKeyStore(KeyStore):
    def __init__(self) -> None:
        self._keys: dict[str, SecretBytes] = {}

    def put_key(self, key_id: str, secret: SecretBytes) -> None:
        key = require_text(key_id, "key_id")
        if not isinstance(secret, SecretBytes):
            raise KeyStoreError("secret must be SecretBytes")
        self._keys[key] = secret

    def get_key(self, key_id: str) -> SecretBytes:
        key = require_text(key_id, "key_id")
        if key not in self._keys:
            raise KeyStoreError("key_id not found")
        return self._keys[key]

    def delete_key(self, key_id: str) -> None:
        key = require_text(key_id, "key_id")
        if key not in self._keys:
            raise KeyStoreError("key_id not found")
        del self._keys[key]

    def list_keys(self) -> list[str]:
        return sorted(self._keys.keys())
