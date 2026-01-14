from __future__ import annotations

from dataclasses import dataclass

from l0_reputation.errors import ValidationError
from l0_reputation.events import RepEvent, RepEventKind
from l0_reputation.hashing import compare_digest, ensure_bytes32, framed, sha256


@dataclass(frozen=True)
class RepState:
    context_id: bytes
    pseudonym_id: bytes
    events: tuple[RepEvent, ...]
    score: int
    root: bytes

    def __post_init__(self) -> None:
        object.__setattr__(self, "context_id", ensure_bytes32(self.context_id, "context_id"))
        object.__setattr__(self, "pseudonym_id", ensure_bytes32(self.pseudonym_id, "pseudonym_id"))
        if not isinstance(self.events, tuple):
            raise ValidationError("events must be tuple")
        for event in self.events:
            if not isinstance(event, RepEvent):
                raise ValidationError("event must be RepEvent")
            if not compare_digest(event.context_id, self.context_id):
                raise ValidationError("event context mismatch")
            if not compare_digest(event.pseudonym_id, self.pseudonym_id):
                raise ValidationError("event pseudonym mismatch")
        if not isinstance(self.score, int) or isinstance(self.score, bool):
            raise ValidationError("score must be int")
        object.__setattr__(self, "root", ensure_bytes32(self.root, "root"))
        expected = recompute_root(self)
        if not compare_digest(self.root, expected):
            raise ValidationError("root mismatch")


def empty_state(context_id: bytes, pseudonym_id: bytes) -> RepState:
    context = ensure_bytes32(context_id, "context_id")
    pseudo = ensure_bytes32(pseudonym_id, "pseudonym_id")
    state = RepState(
        context_id=context,
        pseudonym_id=pseudo,
        events=(),
        score=0,
        root=_compute_root(context, pseudo, (), 0),
    )
    return state


def recompute_root(state: RepState) -> bytes:
    return _compute_root(state.context_id, state.pseudonym_id, state.events, state.score)


def _compute_root(
    context_id: bytes,
    pseudonym_id: bytes,
    events: tuple[RepEvent, ...],
    score: int,
) -> bytes:
    event_ids = sorted(event.event_id for event in events)
    score_bytes = str(score).encode("ascii")
    root = sha256(
        framed(
            [
                b"NYX:REP:ROOT:v1",
                ensure_bytes32(context_id, "context_id"),
                ensure_bytes32(pseudonym_id, "pseudonym_id"),
                score_bytes,
                *event_ids,
            ]
        )
    )
    return ensure_bytes32(root, "root")


def apply_event(state: RepState, event: RepEvent) -> RepState:
    if not isinstance(state, RepState):
        raise ValidationError("state must be RepState")
    if not isinstance(event, RepEvent):
        raise ValidationError("event must be RepEvent")
    if not compare_digest(state.context_id, event.context_id):
        raise ValidationError("context mismatch")
    if not compare_digest(state.pseudonym_id, event.pseudonym_id):
        raise ValidationError("pseudonym mismatch")
    score = state.score
    if event.kind == RepEventKind.EARN:
        score += event.amount
    elif event.kind in (RepEventKind.SPEND, RepEventKind.SLASH):
        score -= event.amount
    else:
        raise ValidationError("unsupported event kind")
    new_events = state.events + (event,)
    root = _compute_root(state.context_id, state.pseudonym_id, new_events, score)
    return RepState(
        context_id=state.context_id,
        pseudonym_id=state.pseudonym_id,
        events=new_events,
        score=score,
        root=root,
    )
