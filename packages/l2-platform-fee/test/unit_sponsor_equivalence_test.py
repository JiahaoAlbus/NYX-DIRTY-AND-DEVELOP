import sys
from pathlib import Path
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = REPO_ROOT / "packages" / "l2-platform-fee" / "src"
ECON_DIR = REPO_ROOT / "packages" / "l2-economics" / "src"
for path in (SRC_DIR, ECON_DIR):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from action import ActionDescriptor, ActionKind  # noqa: E402
from engine import FeeEngineV0  # noqa: E402
from l2_platform_fee.fee_hook import quote_platform_fee, sponsor_platform_fee  # noqa: E402


class SponsorEquivalenceTests(unittest.TestCase):
    def test_sponsor_keeps_amounts(self):
        action = ActionDescriptor(
            kind=ActionKind.STATE_MUTATION,
            module="platform-fee",
            action="mutate",
            payload={"op": "set", "k": "a", "v": "b"},
        )
        engine = FeeEngineV0()
        quote = quote_platform_fee(engine, action, payer="payer-a", platform_fee_amount=2)
        sponsored = sponsor_platform_fee(engine, quote, new_payer="payer-b")
        self.assertEqual(quote.platform_fee_amount, sponsored.platform_fee_amount)
        self.assertEqual(quote.protocol_quote.fee_vector, sponsored.protocol_quote.fee_vector)
        self.assertEqual(quote.total_due, sponsored.total_due)


if __name__ == "__main__":
    unittest.main()
