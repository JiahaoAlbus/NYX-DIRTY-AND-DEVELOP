from __future__ import annotations

from dataclasses import dataclass

from wallet_kernel.errors import ValidationError


@dataclass(frozen=True)
class SecretBytes:
    _value: bytes

    def __post_init__(self) -> None:
        if not isinstance(self._value, bytes):
            raise ValidationError("secret must be bytes")
        if len(self._value) == 0:
            raise ValidationError("secret must be non-empty")

    def __repr__(self) -> str:
        return "SecretBytes(***)"

    def __str__(self) -> str:
        return self.__repr__()

    def _raw(self) -> bytes:
        return self._value

    def __getstate__(self):
        raise TypeError("SecretBytes is not serializable")

    def __reduce__(self):
        raise TypeError("SecretBytes is not serializable")
