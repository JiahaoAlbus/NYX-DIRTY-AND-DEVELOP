from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

from wallet_kernel.canonical import require_text
from wallet_kernel.errors import PolicyError

if TYPE_CHECKING:
    from wallet_kernel.kernel import TxRequest


@dataclass(frozen=True)
class Capability:
    label: str

    def __post_init__(self) -> None:
        try:
            require_text(self.label, "capability")
        except Exception as exc:
            raise PolicyError(str(exc)) from exc

    def __getstate__(self):
        raise TypeError("Capability is not serializable")

    def __reduce__(self):
        raise TypeError("Capability is not serializable")


class ActionPolicy(ABC):
    @abstractmethod
    def authorize(self, request: "TxRequest", capability: Capability | None) -> bool:
        raise NotImplementedError


class DenyAllPolicy(ActionPolicy):
    def authorize(self, request: "TxRequest", capability: Capability | None) -> bool:
        return False
