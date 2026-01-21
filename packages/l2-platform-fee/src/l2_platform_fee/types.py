from __future__ import annotations

from dataclasses import dataclass

from .errors import PlatformFeeError
from quote import FeeQuote, FeeReceipt


@dataclass(frozen=True)
class PlatformFeeQuote:
    protocol_quote: FeeQuote
    platform_fee_amount: int
    total_due: int
    payer: str

    def __post_init__(self) -> None:
        if not isinstance(self.protocol_quote, FeeQuote):
            raise PlatformFeeError("protocol_quote must be FeeQuote")
        if not isinstance(self.platform_fee_amount, int) or isinstance(self.platform_fee_amount, bool):
            raise PlatformFeeError("platform_fee_amount must be int")
        if self.platform_fee_amount < 0:
            raise PlatformFeeError("platform_fee_amount must be >= 0")
        if not isinstance(self.total_due, int) or isinstance(self.total_due, bool):
            raise PlatformFeeError("total_due must be int")
        if self.total_due < 0:
            raise PlatformFeeError("total_due must be >= 0")
        if self.payer != self.protocol_quote.payer:
            raise PlatformFeeError("payer mismatch")
        expected = self.protocol_quote.fee_vector.total() + self.platform_fee_amount
        if self.total_due != expected:
            raise PlatformFeeError("total_due mismatch")


@dataclass(frozen=True)
class PlatformFeeReceipt:
    quote_hash: bytes
    protocol_receipt: FeeReceipt
    platform_fee_amount: int
    total_paid: int
    payer: str

    def __post_init__(self) -> None:
        if not isinstance(self.protocol_receipt, FeeReceipt):
            raise PlatformFeeError("protocol_receipt must be FeeReceipt")
        if not isinstance(self.platform_fee_amount, int) or isinstance(self.platform_fee_amount, bool):
            raise PlatformFeeError("platform_fee_amount must be int")
        if self.platform_fee_amount < 0:
            raise PlatformFeeError("platform_fee_amount must be >= 0")
        if not isinstance(self.total_paid, int) or isinstance(self.total_paid, bool):
            raise PlatformFeeError("total_paid must be int")
        if self.total_paid < 0:
            raise PlatformFeeError("total_paid must be >= 0")
        if self.payer != self.protocol_receipt.payer:
            raise PlatformFeeError("payer mismatch")
        if self.quote_hash != self.protocol_receipt.quote_hash:
            raise PlatformFeeError("quote_hash mismatch")
