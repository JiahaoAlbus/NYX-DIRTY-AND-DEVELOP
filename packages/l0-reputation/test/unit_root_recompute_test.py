import sys
from pathlib import Path
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = REPO_ROOT / "packages" / "l0-reputation" / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from l0_reputation.events import RepEventKind  # noqa: E402
from l0_reputation.hashing import compare_digest, sha256  # noqa: E402
from l0_reputation.kernel import (  # noqa: E402
    DEFAULT_REP_CONTEXT_ID,
    apply_event,
    initial_state,
    new_event,
    new_pseudonym,
    recompute_root,
)


class RootRecomputeTests(unittest.TestCase):
    def test_recompute_matches_state_root(self):
        secret = sha256(b"root-secret")
        pseudo = new_pseudonym(secret, DEFAULT_REP_CONTEXT_ID)
        state = initial_state(DEFAULT_REP_CONTEXT_ID, pseudo)
        events = [
            new_event(
                context_id=DEFAULT_REP_CONTEXT_ID,
                pseudonym_id=pseudo,
                kind=RepEventKind.EARN,
                amount=5,
                nonce=sha256(b"root-nonce-1"),
            ),
            new_event(
                context_id=DEFAULT_REP_CONTEXT_ID,
                pseudonym_id=pseudo,
                kind=RepEventKind.SPEND,
                amount=2,
                nonce=sha256(b"root-nonce-2"),
            ),
            new_event(
                context_id=DEFAULT_REP_CONTEXT_ID,
                pseudonym_id=pseudo,
                kind=RepEventKind.SLASH,
                amount=1,
                nonce=sha256(b"root-nonce-3"),
            ),
        ]
        state_a = state
        for event in events:
            state_a = apply_event(state_a, event)
        self.assertTrue(compare_digest(state_a.root, recompute_root(state_a)))

        state_b = state
        for event in (events[2], events[0], events[1]):
            state_b = apply_event(state_b, event)
        self.assertTrue(compare_digest(state_a.root, state_b.root))


if __name__ == "__main__":
    unittest.main()
