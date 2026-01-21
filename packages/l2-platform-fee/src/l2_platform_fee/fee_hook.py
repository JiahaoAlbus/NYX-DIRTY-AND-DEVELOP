from __future__ import annotations

from action import ActionDescriptor, ActionKind
from engine import FeeEngineError, FeeEngineV0
from fee import FeeVector
from quote import FeePayment

from .errors import PlatformFeeError
from .types import PlatformFeeQuote, PlatformFeeReceipt


def _require_engine(engine: object) -> FeeEngineV0:
    if not isinstance(engine, FeeEngineV0):
        raise PlatformFeeError("engine must be FeeEngineV0")
    return engine


def _require_int(value: object, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise PlatformFeeError(f"{name} must be int")
    return value


def quote_platform_fee(
    engine: FeeEngineV0,
    action: ActionDescriptor,
    payer: str,
    platform_fee_amount: int,
) -> PlatformFeeQuote:
    _require_engine(engine)
    if not isinstance(action, ActionDescriptor):
        raise PlatformFeeError("action must be ActionDescriptor")
    amount = _require_int(platform_fee_amount, "platform_fee_amount")
    if amount < 0:
        raise PlatformFeeError("platform_fee_amount must be >= 0")
    try:
        protocol_quote = engine.quote(action, payer)
    except FeeEngineError as exc:
        raise PlatformFeeError(str(exc)) from exc
    protocol_total = protocol_quote.fee_vector.total()
    if action.kind == ActionKind.STATE_MUTATION and protocol_total <= 0:
        raise PlatformFeeError("protocol fee must be > 0 for mutation")
    total_due = protocol_total + amount
    return PlatformFeeQuote(
        protocol_quote=protocol_quote,
        platform_fee_amount=amount,
        total_due=total_due,
        payer=protocol_quote.payer,
    )


def sponsor_platform_fee(
    engine: FeeEngineV0,
    quote: PlatformFeeQuote,
    new_payer: str,
) -> PlatformFeeQuote:
    _require_engine(engine)
    if not isinstance(quote, PlatformFeeQuote):
        raise PlatformFeeError("quote must be PlatformFeeQuote")
    try:
        sponsored = engine.sponsor(quote.protocol_quote, new_payer)
    except FeeEngineError as exc:
        raise PlatformFeeError(str(exc)) from exc
    total_due = sponsored.fee_vector.total() + quote.platform_fee_amount
    return PlatformFeeQuote(
        protocol_quote=sponsored,
        platform_fee_amount=quote.platform_fee_amount,
        total_due=total_due,
        payer=sponsored.payer,
    )


def enforce_platform_fee(
    engine: FeeEngineV0,
    quote: PlatformFeeQuote,
    paid_protocol_vector: FeeVector,
    paid_platform_amount: int,
    payer: str,
) -> PlatformFeeReceipt:
    _require_engine(engine)
    if not isinstance(quote, PlatformFeeQuote):
        raise PlatformFeeError("quote must be PlatformFeeQuote")
    if not isinstance(paid_protocol_vector, FeeVector):
        raise PlatformFeeError("paid_protocol_vector must be FeeVector")
    amount = _require_int(paid_platform_amount, "paid_platform_amount")
    if payer != quote.payer:
        raise PlatformFeeError("payer mismatch")
    if paid_protocol_vector != quote.protocol_quote.fee_vector:
        raise PlatformFeeError("paid_protocol_vector mismatch")
    if amount != quote.platform_fee_amount:
        raise PlatformFeeError("paid_platform_amount mismatch")
    payment = FeePayment(
        payer=quote.payer,
        quote_hash=quote.protocol_quote.quote_hash,
        paid_vector=paid_protocol_vector,
    )
    try:
        protocol_receipt = engine.enforce(quote.protocol_quote, payment)
    except FeeEngineError as exc:
        raise PlatformFeeError(str(exc)) from exc
    total_paid = paid_protocol_vector.total() + amount
    if total_paid != quote.total_due:
        raise PlatformFeeError("total_paid mismatch")
    return PlatformFeeReceipt(
        quote_hash=quote.protocol_quote.quote_hash,
        protocol_receipt=protocol_receipt,
        platform_fee_amount=amount,
        total_paid=total_paid,
        payer=quote.payer,
    )
