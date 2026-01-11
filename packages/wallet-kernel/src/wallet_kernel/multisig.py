from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

from wallet_kernel.canonical import require_text
from wallet_kernel.errors import PolicyError

if TYPE_CHECKING:
    from wallet_kernel.kernel import TxRequest


class MultiSigPolicy(ABC):
    @abstractmethod
    def required_signers(self) -> tuple[str, ...]:
        raise NotImplementedError

    @abstractmethod
    def threshold(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def authorize(self, request: "TxRequest") -> bool:
        raise NotImplementedError


@dataclass(frozen=True)
class SingleSigPolicy(MultiSigPolicy):
    signer_id: str

    def __post_init__(self) -> None:
        try:
            require_text(self.signer_id, "signer_id")
        except Exception as exc:
            raise PolicyError(str(exc)) from exc

    def required_signers(self) -> tuple[str, ...]:
        return (self.signer_id,)

    def threshold(self) -> int:
        return 1

    def authorize(self, request: "TxRequest") -> bool:
        return True
