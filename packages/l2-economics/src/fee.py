from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from action import ActionKind
from canonical import CanonicalizationError, canonicalize


class FeeComponentId(Enum):
    BASE = "base"
    BYTES = "bytes"
    COMPUTE = "compute"


_COMPONENT_ORDER = (
    FeeComponentId.BASE,
    FeeComponentId.BYTES,
    FeeComponentId.COMPUTE,
)
_COMPONENT_INDEX = {component: index for index, component in enumerate(_COMPONENT_ORDER)}


class FeeError(ValueError):
    pass


@dataclass(frozen=True)
class FeeVector:
    components: tuple[tuple[FeeComponentId, int], ...]

    def __post_init__(self) -> None:
        if not isinstance(self.components, tuple):
            raise FeeError("components must be a tuple")
        seen: set[FeeComponentId] = set()
        normalized: list[tuple[FeeComponentId, int]] = []
        for entry in self.components:
            if not isinstance(entry, tuple) or len(entry) != 2:
                raise FeeError("component entry must be a (FeeComponentId, int) tuple")
            component, amount = entry
            if not isinstance(component, FeeComponentId):
                raise FeeError("component id must be FeeComponentId")
            if not isinstance(amount, int) or isinstance(amount, bool):
                raise FeeError("component amount must be int")
            if amount < 0:
                raise FeeError("component amount must be >= 0")
            if component in seen:
                raise FeeError("component id must be unique")
            seen.add(component)
            normalized.append((component, amount))
        normalized.sort(key=lambda pair: _COMPONENT_INDEX[pair[0]])
        object.__setattr__(self, "components", tuple(normalized))

    @classmethod
    def for_action(
        cls,
        action_kind: ActionKind,
        components: tuple[tuple[FeeComponentId, int], ...],
    ) -> "FeeVector":
        if not isinstance(action_kind, ActionKind):
            raise FeeError("action_kind must be ActionKind")
        vector = cls(components)
        if action_kind == ActionKind.STATE_MUTATION:
            base_amount = vector.get(FeeComponentId.BASE)
            if base_amount <= 0:
                raise FeeError("BASE fee must be > 0 for mutations")
            if vector.total() <= 0:
                raise FeeError("total fee must be > 0 for mutations")
        return vector

    def total(self) -> int:
        return sum(amount for _, amount in self.components)

    def get(self, component: FeeComponentId) -> int:
        for entry_component, amount in self.components:
            if entry_component == component:
                return amount
        return 0

    def is_zero(self) -> bool:
        return self.total() == 0

    def canonical_obj(self) -> list[dict[str, object]]:
        return [
            {"component": component.value, "amount": amount}
            for component, amount in self.components
        ]

    def canonical_bytes(self) -> bytes:
        try:
            return canonicalize(self.canonical_obj())
        except CanonicalizationError as exc:
            raise FeeError(str(exc)) from exc

    def sha256(self) -> bytes:
        from hashing import sha256

        return sha256(self.canonical_bytes())
