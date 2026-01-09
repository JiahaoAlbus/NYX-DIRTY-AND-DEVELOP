import os
import random
import string
import sys
import unittest

SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from action import ActionDescriptor, ActionKind  # noqa: E402
from engine import FeeEngineV0  # noqa: E402
from fee import FeeComponentId, FeeError, FeeVector  # noqa: E402
from hashing import compare_digest  # noqa: E402

RNG = random.Random(2024)
PROPERTY_N = 2000
PAYERS_PER_ACTION = 10


def _random_string(rng: random.Random, length: int = 12) -> str:
    alphabet = string.ascii_lowercase + string.digits
    return "s-" + "".join(rng.choice(alphabet) for _ in range(length))


def _random_value(rng: random.Random, depth: int) -> object:
    if depth <= 0:
        return rng.choice([None, True, False, rng.randint(0, 10_000), _random_string(rng, 6)])
    selector = rng.randint(0, 5)
    if selector == 0:
        return rng.randint(0, 10_000)
    if selector == 1:
        return rng.choice([True, False])
    if selector == 2:
        return _random_string(rng, 6)
    if selector == 3:
        return None
    if selector == 4:
        return [_random_value(rng, depth - 1) for _ in range(rng.randint(0, 3))]
    return {
        _random_string(rng, 4): _random_value(rng, depth - 1)
        for _ in range(rng.randint(0, 3))
    }


def _random_action(rng: random.Random) -> ActionDescriptor:
    kind = ActionKind.STATE_MUTATION if rng.random() < 0.7 else ActionKind.READ_ONLY
    payload = {
        "amount": rng.randint(0, 10_000),
        "note": _random_value(rng, 2),
    }
    metadata = {"trace": _random_string(rng, 8)} if rng.random() < 0.5 else None
    return ActionDescriptor(
        kind=kind,
        module="l2.economics",
        action=_random_string(rng, 10),
        payload=payload,
        metadata=metadata,
    )


class FeeInvariantPropertyTests(unittest.TestCase):
    def test_fee_invariants_property(self):
        engine = FeeEngineV0()
        for _ in range(PROPERTY_N):
            action = _random_action(RNG)
            base_payer = _random_string(RNG, 6)
            quote = engine.quote(action, base_payer)
            if action.kind == ActionKind.STATE_MUTATION:
                self.assertGreater(quote.fee_vector.total(), 0)
                self.assertGreater(quote.fee_vector.get(FeeComponentId.BASE), 0)

            for index in range(PAYERS_PER_ACTION):
                payer = f"payer-{index}-{_random_string(RNG, 4)}"
                next_quote = engine.quote(action, payer)
                self.assertEqual(next_quote.fee_vector, quote.fee_vector)

            for index in range(PAYERS_PER_ACTION):
                payer = f"sponsor-{index}-{_random_string(RNG, 4)}"
                sponsored = engine.sponsor(quote, payer)
                self.assertEqual(sponsored.fee_vector, quote.fee_vector)
                self.assertTrue(compare_digest(sponsored.action_hash, quote.action_hash))

            with self.assertRaises(FeeError):
                FeeVector.for_action(
                    ActionKind.STATE_MUTATION,
                    (
                        (FeeComponentId.BASE, 0),
                        (FeeComponentId.BYTES, 0),
                        (FeeComponentId.COMPUTE, 0),
                    ),
                )


if __name__ == "__main__":
    unittest.main()
