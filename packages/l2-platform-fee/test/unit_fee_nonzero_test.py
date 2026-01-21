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
from l2_platform_fee.fee_hook import quote_platform_fee  # noqa: E402


class FeeNonZeroTests(unittest.TestCase):
    def test_fee_nonzero_for_mutation(self):
        action = ActionDescriptor(
            kind=ActionKind.STATE_MUTATION,
            module="platform-fee",
            action="mutate",
            payload={"op": "set", "k": "a", "v": "b"},
        )
        engine = FeeEngineV0()
        quote = quote_platform_fee(engine, action, payer="payer", platform_fee_amount=1)
        self.assertGreater(quote.protocol_quote.fee_vector.total(), 0)
        self.assertGreater(quote.total_due, 0)


if __name__ == "__main__":
    unittest.main()
