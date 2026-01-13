from __future__ import annotations

from l2_private_ledger.actions import ActionKind, LedgerAction, PrivateMint, PrivateSpend
from l2_private_ledger.errors import DoubleSpendError, LedgerError, ValidationError
from l2_private_ledger.state import LedgerState, recompute_root
from l2_private_ledger.trace import LedgerTrace, LedgerTraceEntry
from l2_private_ledger.types import ensure_bytes32


def apply_action(state: LedgerState, action: LedgerAction) -> LedgerState:
    if not isinstance(state, LedgerState):
        raise ValidationError("state must be LedgerState")
    if not isinstance(action, LedgerAction):
        raise ValidationError("action must be LedgerAction")

    if action.kind == ActionKind.PRIVATE_MINT:
        payload = action.payload
        assert isinstance(payload, PrivateMint)
        commitment = ensure_bytes32(payload.commitment, "commitment")
        if commitment in state.commitments:
            raise LedgerError("commitment already exists")
        return LedgerState(
            commitments=frozenset(set(state.commitments) | {commitment}),
            nullifiers=state.nullifiers,
        )

    if action.kind == ActionKind.PRIVATE_SPEND:
        payload = action.payload
        assert isinstance(payload, PrivateSpend)
        nullifier = ensure_bytes32(payload.nullifier, "nullifier")
        if nullifier in state.nullifiers:
            raise DoubleSpendError("nullifier already spent")
        return LedgerState(
            commitments=state.commitments,
            nullifiers=frozenset(set(state.nullifiers) | {nullifier}),
        )

    raise ValidationError("unsupported action kind")


def run_actions_with_trace(
    initial_state: LedgerState,
    actions: list[LedgerAction],
) -> tuple[LedgerState, LedgerTrace]:
    state = initial_state
    entries: list[LedgerTraceEntry] = []
    for action in actions:
        state = apply_action(state, action)
        root = recompute_root(state)
        entries.append(LedgerTraceEntry(action=action, after_root=root))
    trace = LedgerTrace(entries=tuple(entries), final_state=state)
    return state, trace
