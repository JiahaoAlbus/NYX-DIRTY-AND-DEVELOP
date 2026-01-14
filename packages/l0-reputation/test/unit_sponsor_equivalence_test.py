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

from engine import FeeEngineV0  # noqa: E402
from l0_reputation.events import RepEventKind  # noqa: E402
from l0_reputation.fee_binding import quote_fee_for_rep_event  # noqa: E402
from l0_reputation.hashing import sha256  # noqa: E402
from l0_reputation.kernel import (  # noqa: E402
    DEFAULT_REP_CONTEXT_ID,
    initial_state,
    new_event,
    new_pseudonym,
)


class SponsorEquivalenceTests(unittest.TestCase):
    def test_payer_change_keeps_amount(self):
        engine = FeeEngineV0()
        pseudo = new_pseudonym(sha256(b"sponsor-secret"), DEFAULT_REP_CONTEXT_ID)
        state = initial_state(DEFAULT_REP_CONTEXT_ID, pseudo)
        event = new_event(
            context_id=DEFAULT_REP_CONTEXT_ID,
            pseudonym_id=pseudo,
            kind=RepEventKind.SPEND,
            amount=4,
            nonce=sha256(b"sponsor-nonce"),
        )
        quote_a = quote_fee_for_rep_event(engine, state.root, event, payer="payer-a")
        quote_b = quote_fee_for_rep_event(engine, state.root, event, payer="payer-b")
        self.assertEqual(quote_a.fee_vector.components, quote_b.fee_vector.components)

        sponsored = engine.sponsor(quote_a, "payer-b")
        self.assertEqual(sponsored.payer, "payer-b")
        self.assertEqual(sponsored.fee_vector.components, quote_a.fee_vector.components)


if __name__ == "__main__":
    unittest.main()
