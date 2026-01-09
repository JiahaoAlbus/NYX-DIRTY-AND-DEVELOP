import inspect
import os
import sys
import unittest
from pathlib import Path

SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

import engine as engine_module  # noqa: E402
from action import ActionDescriptor, ActionKind  # noqa: E402
from canonical import (  # noqa: E402
    MAX_CANONICAL_BYTES,
    MAX_CANONICAL_DEPTH,
    CanonicalizationError,
    canonicalize,
)
from engine import FeeEngineV0  # noqa: E402
from fee import FeeComponentId  # noqa: E402
from hashing import compare_digest  # noqa: E402
from quote import FeePayment  # noqa: E402

KEYWORDS = [
    "allowlist",
    "whitelist",
    "bypass",
    "override",
    "admin",
    "debug_free",
    "free_lane",
    "free mode",
]


def _mutation_action() -> ActionDescriptor:
    return ActionDescriptor(
        kind=ActionKind.STATE_MUTATION,
        module="l2.economics",
        action="write_state",
        payload={"delta": 1},
        metadata={"trace": "guard"},
    )


class FeeGuardRegressionTests(unittest.TestCase):
    def test_no_bypass_keywords_in_src(self):
        src_root = Path(__file__).resolve().parents[1] / "src"
        for root, _, files in os.walk(src_root):
            for filename in files:
                if not filename.endswith(".py"):
                    continue
                path = Path(root) / filename
                content = path.read_text(encoding="utf-8", errors="ignore").lower()
                for keyword in KEYWORDS:
                    self.assertNotIn(keyword, content, msg=f"{keyword} found in {path}")

    def test_engine_api_has_no_bypass_params(self):
        banned = ["allow", "whitelist", "bypass", "override", "admin", "debug", "free"]
        for method in ("quote", "sponsor", "enforce"):
            signature = inspect.signature(getattr(FeeEngineV0, method))
            for param in signature.parameters.values():
                name = param.name.lower()
                for token in banned:
                    self.assertNotIn(token, name)

    def test_mutation_fee_nonzero_guard(self):
        engine = FeeEngineV0()
        quote = engine.quote(_mutation_action(), "payer-a")
        self.assertGreater(quote.fee_vector.get(FeeComponentId.BASE), 0)
        self.assertGreater(quote.fee_vector.total(), 0)

    def test_fee_independent_of_payer_guard(self):
        engine = FeeEngineV0()
        action = _mutation_action()
        first = engine.quote(action, "payer-a")
        second = engine.quote(action, "payer-b")
        self.assertEqual(first.fee_vector, second.fee_vector)

    def test_sponsor_equivalence_guard(self):
        engine = FeeEngineV0()
        quote = engine.quote(_mutation_action(), "payer-a")
        sponsored = engine.sponsor(quote, "payer-b")
        self.assertEqual(quote.fee_vector, sponsored.fee_vector)
        self.assertTrue(compare_digest(quote.action_hash, sponsored.action_hash))

    def test_canonicalization_rejects_weak_types(self):
        with self.assertRaises(CanonicalizationError):
            canonicalize(1.5)
        with self.assertRaises(CanonicalizationError):
            canonicalize(float("nan"))
        with self.assertRaises(CanonicalizationError):
            canonicalize(b"bytes")
        with self.assertRaises(CanonicalizationError):
            canonicalize(bytearray(b"bytes"))
        with self.assertRaises(CanonicalizationError):
            canonicalize("\ud800")
        self.assertNotEqual(canonicalize(True), canonicalize(1))

    def test_canonicalization_guards(self):
        value = "leaf"
        for _ in range(MAX_CANONICAL_DEPTH + 1):
            value = [value]
        with self.assertRaises(CanonicalizationError):
            canonicalize(value)
        payload = {"data": "a" * (MAX_CANONICAL_BYTES + 1)}
        with self.assertRaises(CanonicalizationError):
            canonicalize(payload)

    def test_framed_preimage_anti_ambiguity(self):
        first = ActionDescriptor(
            kind=ActionKind.READ_ONLY,
            module="ab",
            action="c",
            payload={"v": 1},
            metadata=None,
        )
        second = ActionDescriptor(
            kind=ActionKind.READ_ONLY,
            module="a",
            action="bc",
            payload={"v": 1},
            metadata=None,
        )
        self.assertNotEqual(first.framed_preimage(), second.framed_preimage())

    def test_compare_digest_guard(self):
        engine = FeeEngineV0()
        quote = engine.quote(_mutation_action(), "payer-a")
        payment = FeePayment(
            payer=quote.payer,
            quote_hash=quote.quote_hash,
            paid_vector=quote.fee_vector,
        )
        calls = {"count": 0}
        original = engine_module.compare_digest

        def wrapped(left, right):
            calls["count"] += 1
            return original(left, right)

        engine_module.compare_digest = wrapped
        try:
            engine.enforce(quote, payment)
        finally:
            engine_module.compare_digest = original
        self.assertGreater(calls["count"], 0)


if __name__ == "__main__":
    unittest.main()
