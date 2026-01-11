from __future__ import annotations

from abc import ABC, abstractmethod


class SpendLimitPolicy(ABC):
    @abstractmethod
    def check(self, amount_vector: object, window: object) -> bool:
        raise NotImplementedError


class NoSpendLimitPolicy(SpendLimitPolicy):
    def check(self, amount_vector: object, window: object) -> bool:
        return True
