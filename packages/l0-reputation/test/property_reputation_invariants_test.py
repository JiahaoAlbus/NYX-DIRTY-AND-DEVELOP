import os
import random
import sys
from pathlib import Path
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = REPO_ROOT / "packages" / "l0-reputation" / "src"
ECON_DIR = REPO_ROOT / "packages" / "l2-economics" / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(ECON_DIR) not in sys.path:
    sys.path.insert(0, str(ECON_DIR))

from l0_reputation.errors import ValidationError  # noqa: E402
from l0_reputation.events import RepEventKind  # noqa: E402
from l0_reputation.hashing import compare_digest, sha256  # noqa: E402
from l0_reputation.kernel import (  # noqa: E402
    apply_event,
    initial_state,
    new_event,
    new_pseudonym,
    recompute_root,
)

PROPERTY_N = int(os.environ.get("PROPERTY_N", "2000"))


def rand_bytes32(rng: random.Random) -> bytes:
    return bytes(rng.getrandbits(8) for _ in range(32))


class PropertyReputationInvariantTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        print(f"PROPERTY_N={PROPERTY_N}")

    def test_invariants_hold(self):
        rng = random.Random(9071)
        kinds = [RepEventKind.EARN, RepEventKind.SPEND, RepEventKind.SLASH]
        for _ in range(PROPERTY_N):
            context = sha256(rand_bytes32(rng))
            secret = rand_bytes32(rng)
            pseudo = new_pseudonym(secret, context)
            state = initial_state(context, pseudo)
            events = []
            event_count = rng.randint(3, 8)
            for _idx in range(event_count):
                kind = rng.choice(kinds)
                amount = rng.randint(1, 20)
                nonce = rand_bytes32(rng)
                event = new_event(
                    context_id=context,
                    pseudonym_id=pseudo,
                    kind=kind,
                    amount=amount,
                    nonce=nonce,
                )
                events.append(event)
                state = apply_event(state, event)

            self.assertTrue(compare_digest(state.root, recompute_root(state)))

            events_shuffled = list(events)
            rng.shuffle(events_shuffled)
            state_alt = initial_state(context, pseudo)
            for event in events_shuffled:
                state_alt = apply_event(state_alt, event)
            self.assertTrue(compare_digest(state.root, state_alt.root))

            other_context = sha256(b"alt" + context)
            other_pseudo = new_pseudonym(rand_bytes32(rng), other_context)
            bad_event = new_event(
                context_id=other_context,
                pseudonym_id=other_pseudo,
                kind=rng.choice(kinds),
                amount=rng.randint(1, 20),
                nonce=rand_bytes32(rng),
            )
            with self.assertRaises(ValidationError):
                apply_event(state, bad_event)


if __name__ == "__main__":
    unittest.main()
