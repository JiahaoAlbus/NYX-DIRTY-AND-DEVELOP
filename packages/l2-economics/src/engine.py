from __future__ import annotations

from action import ActionDescriptor, ActionError, ActionKind
from canonical import CanonicalizationError, require_text
from fee import FeeComponentId, FeeError, FeeVector
from hashing import compare_digest
from quote import FeePayment, FeeQuote, FeeReceipt, QuoteError, create_quote, create_receipt


class FeeEngineError(ValueError):
    pass


class FeeEngineV0:
    BASE_FEE = 1

    def quote(self, action: ActionDescriptor, payer: str) -> FeeQuote:
        if not isinstance(action, ActionDescriptor):
            raise FeeEngineError("action must be ActionDescriptor")
        try:
            require_text(payer, "payer")
        except CanonicalizationError as exc:
            raise FeeEngineError(str(exc)) from exc
        fee_vector = self._calculate_fee_vector(action)
        try:
            return create_quote(action.action_hash(), fee_vector, payer)
        except (QuoteError, FeeError, ActionError) as exc:
            raise FeeEngineError(str(exc)) from exc

    def sponsor(self, quote: FeeQuote, new_payer: str) -> FeeQuote:
        if not isinstance(quote, FeeQuote):
            raise FeeEngineError("quote must be FeeQuote")
        try:
            require_text(new_payer, "new_payer")
        except CanonicalizationError as exc:
            raise FeeEngineError(str(exc)) from exc
        try:
            return create_quote(quote.action_hash, quote.fee_vector, new_payer)
        except QuoteError as exc:
            raise FeeEngineError(str(exc)) from exc

    def enforce(self, quote: FeeQuote, payment: FeePayment) -> FeeReceipt:
        if not isinstance(quote, FeeQuote):
            raise FeeEngineError("quote must be FeeQuote")
        if not isinstance(payment, FeePayment):
            raise FeeEngineError("payment must be FeePayment")
        if not compare_digest(payment.quote_hash, quote.quote_hash):
            raise FeeEngineError("quote_hash mismatch")
        if payment.payer != quote.payer:
            raise FeeEngineError("payer mismatch")
        if payment.paid_vector != quote.fee_vector:
            raise FeeEngineError("paid_vector mismatch")
        try:
            return create_receipt(quote, payment)
        except QuoteError as exc:
            raise FeeEngineError(str(exc)) from exc

    def _calculate_fee_vector(self, action: ActionDescriptor) -> FeeVector:
        payload_size = len(action.canonical_bytes())
        if action.kind == ActionKind.READ_ONLY:
            components = (
                (FeeComponentId.BASE, 0),
                (FeeComponentId.BYTES, 0),
                (FeeComponentId.COMPUTE, 0),
            )
            return FeeVector.for_action(action.kind, components)
        if action.kind == ActionKind.STATE_MUTATION:
            components = (
                (FeeComponentId.BASE, self.BASE_FEE),
                (FeeComponentId.BYTES, payload_size),
                (FeeComponentId.COMPUTE, 0),
            )
            return FeeVector.for_action(action.kind, components)
        raise FeeEngineError("unsupported action kind")
