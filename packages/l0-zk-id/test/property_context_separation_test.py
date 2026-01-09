import os
import random
import string
import sys
import unittest

SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from prover.mock import prove_mock  # noqa: E402
from verifier import MockProofAdapter, verify  # noqa: E402

RNG = random.Random(1337)
PROPERTY_N = 1000
C2_SAMPLES = 10


def _random_bytes32(rng: random.Random) -> bytes:
    return bytes(rng.getrandbits(8) for _ in range(32))


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


def _random_public_inputs(rng: random.Random) -> dict:
    inputs = {
        "a": _random_value(rng, 2),
        "b": _random_value(rng, 2),
        "c": _random_value(rng, 1),
    }
    if "_mock_witness_hash" in inputs:
        inputs["c"] = "safe"
    return inputs


def _random_witness(rng: random.Random) -> dict:
    return {
        "w": _random_value(rng, 2),
        "x": _random_value(rng, 1),
    }


class ContextSeparationPropertyTests(unittest.TestCase):
    def test_context_separation_property(self):
        adapter = MockProofAdapter()
        for _ in range(PROPERTY_N):
            context_id = _random_bytes32(RNG)
            nonce = _random_bytes32(RNG)
            statement_id = _random_string(RNG, 10)
            public_inputs = _random_public_inputs(RNG)
            witness = _random_witness(RNG)

            envelope = prove_mock(
                statement_id=statement_id,
                context_id=context_id,
                nonce=nonce,
                public_inputs=public_inputs,
                witness=witness,
            )
            self.assertTrue(verify(envelope, context_id, statement_id, adapter))

            samples = 0
            while samples < C2_SAMPLES:
                other_context = _random_bytes32(RNG)
                if other_context == context_id:
                    continue
                self.assertFalse(verify(envelope, other_context, statement_id, adapter))
                samples += 1


if __name__ == "__main__":
    unittest.main()
