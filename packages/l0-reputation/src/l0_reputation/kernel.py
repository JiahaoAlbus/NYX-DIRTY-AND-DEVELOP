from __future__ import annotations

from l0_reputation.errors import ValidationError
from l0_reputation.events import RepEvent, RepEventKind, compute_event_id
from l0_reputation.hashing import ensure_bytes32, framed, sha256
from l0_reputation.state import RepState, apply_event as _apply_event, empty_state, recompute_root as _recompute_root

DEFAULT_REP_CONTEXT_ID = sha256(b"NYX:CTX:Q3:REPUTATION:v1")


def new_pseudonym(secret_commitment: bytes, context_id: bytes = DEFAULT_REP_CONTEXT_ID) -> bytes:
    context = ensure_bytes32(context_id, "context_id")
    secret = ensure_bytes32(secret_commitment, "secret_commitment")
    pseudonym_id = sha256(
        framed([b"NYX:REP:PSEUDONYM:v1", context, secret])
    )
    return ensure_bytes32(pseudonym_id, "pseudonym_id")


def new_event(
    *,
    context_id: bytes,
    pseudonym_id: bytes,
    kind: RepEventKind,
    amount: int,
    nonce: bytes,
) -> RepEvent:
    event_id = compute_event_id(context_id, pseudonym_id, kind, amount, nonce)
    return RepEvent(
        context_id=context_id,
        pseudonym_id=pseudonym_id,
        kind=kind,
        amount=amount,
        nonce=nonce,
        event_id=event_id,
    )


def apply_event(state: RepState, event: RepEvent) -> RepState:
    return _apply_event(state, event)


def initial_state(context_id: bytes, pseudonym_id: bytes) -> RepState:
    return empty_state(context_id, pseudonym_id)


def recompute_root(state: RepState) -> bytes:
    return _recompute_root(state)
