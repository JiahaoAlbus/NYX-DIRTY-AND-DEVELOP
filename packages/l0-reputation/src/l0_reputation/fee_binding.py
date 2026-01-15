from __future__ import annotations

from l0_reputation.errors import ValidationError
from l0_reputation.events import RepEvent
from l0_reputation.hashing import ensure_bytes32
from l0_reputation.state import RepState

try:
    from action import ActionDescriptor, ActionKind as FeeActionKind
    from engine import FeeEngineV0, FeeEngineError
    from fee import FeeVector
    from quote import FeePayment, FeeQuote, FeeReceipt, QuoteError
except Exception as exc:  # pragma: no cover - handled at runtime
    ActionDescriptor = None  # type: ignore
    FeeActionKind = None  # type: ignore
    FeeEngineV0 = object  # type: ignore
    FeeVector = object  # type: ignore
    FeeQuote = object  # type: ignore
    FeePayment = object  # type: ignore
    FeeReceipt = object  # type: ignore
    _IMPORT_ERROR = exc

    class FeeEngineError(Exception):
        pass

    class QuoteError(Exception):
        pass


def quote_fee_for_rep_event(
    engine: FeeEngineV0,
    state_root: bytes,
    event: RepEvent,
    payer: str,
) -> FeeQuote:
    _require_economics()
    if not isinstance(engine, FeeEngineV0):
        raise ValidationError("engine must be FeeEngineV0")
    if not isinstance(event, RepEvent):
        raise ValidationError("event must be RepEvent")
    root_bytes = ensure_bytes32(state_root, "state_root")

    payload = {
        "context_id": event.context_id.hex(),
        "pseudonym_id": event.pseudonym_id.hex(),
        "event_id": event.event_id.hex(),
        "event_kind": event.kind.value,
        "amount": event.amount,
        "nonce": event.nonce.hex(),
        "state_root": root_bytes.hex(),
        "v": 1,
    }
    descriptor = ActionDescriptor(
        kind=FeeActionKind.STATE_MUTATION,
        module="l0.reputation",
        action="rep_event",
        payload=payload,
        metadata=None,
    )
    try:
        return engine.quote(descriptor, payer)
    except (FeeEngineError, QuoteError) as exc:
        raise ValidationError(str(exc)) from exc


def enforce_fee_for_rep_event(
    engine: FeeEngineV0,
    quote: FeeQuote,
    paid_vector: FeeVector,
    payer: str,
) -> FeeReceipt:
    _require_economics()
    if not isinstance(engine, FeeEngineV0):
        raise ValidationError("engine must be FeeEngineV0")
    if not isinstance(quote, FeeQuote):
        raise ValidationError("quote must be FeeQuote")
    if not isinstance(paid_vector, FeeVector):
        raise ValidationError("paid_vector must be FeeVector")
    if not isinstance(payer, str) or not payer:
        raise ValidationError("payer must be non-empty string")
    payment = FeePayment(payer=payer, quote_hash=quote.quote_hash, paid_vector=paid_vector)
    try:
        return engine.enforce(quote, payment)
    except (FeeEngineError, QuoteError) as exc:
        raise ValidationError(str(exc)) from exc


def _require_economics() -> None:
    if ActionDescriptor is None or FeeActionKind is None:
        raise ValidationError("l2-economics unavailable") from _IMPORT_ERROR
