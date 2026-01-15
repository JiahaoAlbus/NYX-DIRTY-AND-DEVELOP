import sys
from pathlib import Path
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = REPO_ROOT / "packages" / "l0-reputation" / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from l0_reputation.errors import ValidationError  # noqa: E402
from l0_reputation.events import RepEventKind  # noqa: E402
from l0_reputation.hashing import compare_digest, sha256  # noqa: E402
from l0_reputation.kernel import (  # noqa: E402
    DEFAULT_REP_CONTEXT_ID,
    apply_event,
    initial_state,
    new_event,
    new_pseudonym,
)


class ContextBindingTests(unittest.TestCase):
    def test_new_pseudonym_diff_contexts(self):
        secret = sha256(b"rep-secret")
        other_context = sha256(b"rep-context-alt")
        pseudo_main = new_pseudonym(secret, DEFAULT_REP_CONTEXT_ID)
        pseudo_other = new_pseudonym(secret, other_context)
        self.assertFalse(compare_digest(pseudo_main, pseudo_other))

    def test_apply_event_rejects_context_mismatch(self):
        secret = sha256(b"rep-secret-2")
        pseudo = new_pseudonym(secret, DEFAULT_REP_CONTEXT_ID)
        state = initial_state(DEFAULT_REP_CONTEXT_ID, pseudo)
        other_context = sha256(b"rep-context-other")
        other_pseudo = new_pseudonym(sha256(b"rep-secret-3"), other_context)
        event = new_event(
            context_id=other_context,
            pseudonym_id=other_pseudo,
            kind=RepEventKind.EARN,
            amount=3,
            nonce=sha256(b"rep-nonce-1"),
        )
        with self.assertRaises(ValidationError):
            apply_event(state, event)

    def test_apply_event_rejects_pseudonym_mismatch(self):
        secret = sha256(b"rep-secret-4")
        pseudo = new_pseudonym(secret, DEFAULT_REP_CONTEXT_ID)
        state = initial_state(DEFAULT_REP_CONTEXT_ID, pseudo)
        other_pseudo = new_pseudonym(sha256(b"rep-secret-5"), DEFAULT_REP_CONTEXT_ID)
        event = new_event(
            context_id=DEFAULT_REP_CONTEXT_ID,
            pseudonym_id=other_pseudo,
            kind=RepEventKind.SPEND,
            amount=2,
            nonce=sha256(b"rep-nonce-2"),
        )
        with self.assertRaises(ValidationError):
            apply_event(state, event)


if __name__ == "__main__":
    unittest.main()
