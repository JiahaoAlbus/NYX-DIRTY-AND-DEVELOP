from __future__ import annotations

from dataclasses import dataclass

from l2_private_ledger.actions import LedgerAction
from l2_private_ledger.errors import ValidationError
from l2_private_ledger.state import LedgerState, recompute_root
from l2_private_ledger.types import compare_digest, ensure_bytes32


@dataclass(frozen=True)
class LedgerTraceEntry:
    action: LedgerAction
    after_root: bytes

    def __post_init__(self) -> None:
        if not isinstance(self.action, LedgerAction):
            raise ValidationError("trace action must be LedgerAction")
        object.__setattr__(self, "after_root", ensure_bytes32(self.after_root, "after_root"))


@dataclass(frozen=True)
class LedgerTrace:
    entries: tuple[LedgerTraceEntry, ...]
    final_state: LedgerState | None = None

    def __post_init__(self) -> None:
        for entry in self.entries:
            if not isinstance(entry, LedgerTraceEntry):
                raise ValidationError("trace entry invalid")


def replay_and_verify(initial_state: LedgerState, trace: LedgerTrace) -> bool:
    state = initial_state
    for entry in trace.entries:
        state = apply_action(state, entry.action)
        expected_root = recompute_root(state)
        if not compare_digest(expected_root, entry.after_root):
            return False
    return True


def apply_action(state: LedgerState, action: LedgerAction) -> LedgerState:
    from l2_private_ledger.kernel import apply_action as _apply_action

    return _apply_action(state, action)
