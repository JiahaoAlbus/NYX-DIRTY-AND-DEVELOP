from __future__ import annotations

from dataclasses import dataclass

from canonical import CanonicalizationError, canonicalize, require_text
from fee import FeeError, FeeVector
from hashing import bytes32_hex, compare_digest, require_bytes32, sha256


class QuoteError(ValueError):
    pass


def create_quote(action_hash: bytes, fee_vector: FeeVector, payer: str) -> "FeeQuote":
    quote_hash = sha256(_quote_canonical_bytes(action_hash, fee_vector, payer))
    return FeeQuote(
        action_hash=action_hash,
        fee_vector=fee_vector,
        payer=payer,
        quote_hash=quote_hash,
    )


def create_receipt(quote: "FeeQuote", payment: "FeePayment") -> "FeeReceipt":
    receipt_hash = sha256(
        _receipt_canonical_bytes(
            quote.quote_hash,
            quote.action_hash,
            payment.payer,
            payment.paid_vector,
        )
    )
    return FeeReceipt(
        quote_hash=quote.quote_hash,
        action_hash=quote.action_hash,
        payer=payment.payer,
        paid_vector=payment.paid_vector,
        receipt_hash=receipt_hash,
    )


@dataclass(frozen=True)
class FeeQuote:
    action_hash: bytes
    fee_vector: FeeVector
    payer: str
    quote_hash: bytes

    def __post_init__(self) -> None:
        try:
            require_text(self.payer, "payer")
        except CanonicalizationError as exc:
            raise QuoteError(str(exc)) from exc
        try:
            require_bytes32(self.action_hash, "action_hash")
            require_bytes32(self.quote_hash, "quote_hash")
        except Exception as exc:
            raise QuoteError(str(exc)) from exc
        if not isinstance(self.fee_vector, FeeVector):
            raise QuoteError("fee_vector must be FeeVector")
        expected = sha256(self.canonical_bytes())
        if not compare_digest(self.quote_hash, expected):
            raise QuoteError("quote_hash mismatch")

    def canonical_bytes(self) -> bytes:
        return _quote_canonical_bytes(self.action_hash, self.fee_vector, self.payer)

    def sha256(self) -> bytes:
        return sha256(self.canonical_bytes())


@dataclass(frozen=True)
class FeePayment:
    payer: str
    quote_hash: bytes
    paid_vector: FeeVector

    def __post_init__(self) -> None:
        try:
            require_text(self.payer, "payer")
        except CanonicalizationError as exc:
            raise QuoteError(str(exc)) from exc
        try:
            require_bytes32(self.quote_hash, "quote_hash")
        except Exception as exc:
            raise QuoteError(str(exc)) from exc
        if not isinstance(self.paid_vector, FeeVector):
            raise QuoteError("paid_vector must be FeeVector")

    def canonical_bytes(self) -> bytes:
        payload = {
            "payer": self.payer,
            "quote_hash": bytes32_hex(self.quote_hash, "quote_hash"),
            "paid_vector": self.paid_vector.canonical_obj(),
        }
        try:
            return canonicalize(payload)
        except CanonicalizationError as exc:
            raise QuoteError(str(exc)) from exc


@dataclass(frozen=True)
class FeeReceipt:
    quote_hash: bytes
    action_hash: bytes
    payer: str
    paid_vector: FeeVector
    receipt_hash: bytes

    def __post_init__(self) -> None:
        try:
            require_text(self.payer, "payer")
        except CanonicalizationError as exc:
            raise QuoteError(str(exc)) from exc
        try:
            require_bytes32(self.quote_hash, "quote_hash")
            require_bytes32(self.action_hash, "action_hash")
            require_bytes32(self.receipt_hash, "receipt_hash")
        except Exception as exc:
            raise QuoteError(str(exc)) from exc
        if not isinstance(self.paid_vector, FeeVector):
            raise QuoteError("paid_vector must be FeeVector")
        expected = sha256(self.canonical_bytes())
        if not compare_digest(self.receipt_hash, expected):
            raise QuoteError("receipt_hash mismatch")

    def canonical_bytes(self) -> bytes:
        return _receipt_canonical_bytes(
            self.quote_hash,
            self.action_hash,
            self.payer,
            self.paid_vector,
        )

    def sha256(self) -> bytes:
        return sha256(self.canonical_bytes())


def _quote_canonical_bytes(action_hash: bytes, fee_vector: FeeVector, payer: str) -> bytes:
    payload = {
        "action_hash": bytes32_hex(action_hash, "action_hash"),
        "fee_vector": fee_vector.canonical_obj(),
        "payer": payer,
    }
    try:
        return canonicalize(payload)
    except CanonicalizationError as exc:
        raise QuoteError(str(exc)) from exc


def _receipt_canonical_bytes(
    quote_hash: bytes,
    action_hash: bytes,
    payer: str,
    paid_vector: FeeVector,
) -> bytes:
    payload = {
        "quote_hash": bytes32_hex(quote_hash, "quote_hash"),
        "action_hash": bytes32_hex(action_hash, "action_hash"),
        "payer": payer,
        "paid_vector": paid_vector.canonical_obj(),
    }
    try:
        return canonicalize(payload)
    except CanonicalizationError as exc:
        raise QuoteError(str(exc)) from exc
