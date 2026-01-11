from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from wallet_kernel.canonical import require_text
from wallet_kernel.errors import PolicyError


@dataclass(frozen=True)
class RecoveryPlan:
    old_key_id: str
    new_key_id: str
    guardians: tuple[str, ...]

    def __post_init__(self) -> None:
        try:
            require_text(self.old_key_id, "old_key_id")
            require_text(self.new_key_id, "new_key_id")
        except Exception as exc:
            raise PolicyError(str(exc)) from exc
        if not isinstance(self.guardians, tuple):
            raise PolicyError("guardians must be a tuple")
        for guardian in self.guardians:
            try:
                require_text(guardian, "guardian")
            except Exception as exc:
                raise PolicyError(str(exc)) from exc


class SocialRecoveryPolicy(ABC):
    @abstractmethod
    def propose_rotation(
        self, old_key_id: str, new_key_id: str, guardians: tuple[str, ...]
    ) -> RecoveryPlan:
        raise NotImplementedError

    @abstractmethod
    def execute(self, plan: RecoveryPlan, approvals: tuple[str, ...]) -> None:
        raise NotImplementedError


class NoopSocialRecoveryPolicy(SocialRecoveryPolicy):
    def propose_rotation(
        self, old_key_id: str, new_key_id: str, guardians: tuple[str, ...]
    ) -> RecoveryPlan:
        return RecoveryPlan(
            old_key_id=old_key_id,
            new_key_id=new_key_id,
            guardians=guardians,
        )

    def execute(self, plan: RecoveryPlan, approvals: tuple[str, ...]) -> None:
        raise NotImplementedError("social recovery not configured")
