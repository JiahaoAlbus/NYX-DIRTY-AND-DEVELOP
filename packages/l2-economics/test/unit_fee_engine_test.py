import hashlib
import os
import sys
import unittest

SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from action import ActionDescriptor, ActionKind  # noqa: E402
from engine import FeeEngineError, FeeEngineV0  # noqa: E402
from fee import FeeComponentId, FeeVector  # noqa: E402
from hashing import compare_digest  # noqa: E402
from quote import FeePayment  # noqa: E402


def _bytes32(label: str) -> bytes:
    return hashlib.sha256(label.encode("ascii")).digest()


def _mutation_action() -> ActionDescriptor:
    return ActionDescriptor(
        kind=ActionKind.STATE_MUTATION,
        module="l2.economics",
        action="write_state",
        payload={"delta": 1},
        metadata={"trace": "unit"},
    )


def _read_action() -> ActionDescriptor:
    return ActionDescriptor(
        kind=ActionKind.READ_ONLY,
        module="l2.economics",
        action="read_state",
        payload=None,
        metadata=None,
    )


class FeeEngineUnitTests(unittest.TestCase):
    def setUp(self):
        self.engine = FeeEngineV0()

    def test_mutation_fee_nonzero(self):
        quote = self.engine.quote(_mutation_action(), "payer-a")
        self.assertGreater(quote.fee_vector.total(), 0)
        self.assertGreater(quote.fee_vector.get(FeeComponentId.BASE), 0)

    def test_read_only_fee_zero(self):
        quote = self.engine.quote(_read_action(), "payer-a")
        self.assertEqual(quote.fee_vector.total(), 0)
        self.assertTrue(quote.fee_vector.is_zero())

    def test_sponsor_equivalence(self):
        quote = self.engine.quote(_mutation_action(), "payer-a")
        sponsored = self.engine.sponsor(quote, "payer-b")
        self.assertNotEqual(sponsored.payer, quote.payer)
        self.assertEqual(sponsored.fee_vector, quote.fee_vector)
        self.assertTrue(compare_digest(sponsored.action_hash, quote.action_hash))

    def test_enforce_rejects_mismatched_quote_hash(self):
        quote = self.engine.quote(_mutation_action(), "payer-a")
        payment = FeePayment(
            payer=quote.payer,
            quote_hash=_bytes32("other"),
            paid_vector=quote.fee_vector,
        )
        with self.assertRaises(FeeEngineError):
            self.engine.enforce(quote, payment)

    def test_enforce_rejects_mismatched_payer(self):
        quote = self.engine.quote(_mutation_action(), "payer-a")
        payment = FeePayment(
            payer="payer-b",
            quote_hash=quote.quote_hash,
            paid_vector=quote.fee_vector,
        )
        with self.assertRaises(FeeEngineError):
            self.engine.enforce(quote, payment)

    def test_enforce_rejects_mismatched_paid_vector(self):
        quote = self.engine.quote(_mutation_action(), "payer-a")
        wrong_vector = FeeVector(
            (
                (FeeComponentId.BASE, quote.fee_vector.get(FeeComponentId.BASE) + 1),
                (FeeComponentId.BYTES, quote.fee_vector.get(FeeComponentId.BYTES)),
                (FeeComponentId.COMPUTE, quote.fee_vector.get(FeeComponentId.COMPUTE)),
            )
        )
        payment = FeePayment(
            payer=quote.payer,
            quote_hash=quote.quote_hash,
            paid_vector=wrong_vector,
        )
        with self.assertRaises(FeeEngineError):
            self.engine.enforce(quote, payment)

    def test_enforce_accepts_valid_payment(self):
        quote = self.engine.quote(_mutation_action(), "payer-a")
        payment = FeePayment(
            payer=quote.payer,
            quote_hash=quote.quote_hash,
            paid_vector=quote.fee_vector,
        )
        receipt = self.engine.enforce(quote, payment)
        self.assertTrue(compare_digest(receipt.quote_hash, quote.quote_hash))
        self.assertTrue(compare_digest(receipt.action_hash, quote.action_hash))
        self.assertEqual(receipt.paid_vector, quote.fee_vector)
        self.assertTrue(compare_digest(receipt.receipt_hash, receipt.sha256()))


if __name__ == "__main__":
    unittest.main()
