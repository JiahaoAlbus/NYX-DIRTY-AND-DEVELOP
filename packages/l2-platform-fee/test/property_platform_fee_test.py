import os
import random
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


class PlatformFeePropertyTests(unittest.TestCase):
    def test_platform_fee_properties(self):
        n = int(os.environ.get("PROPERTY_N", "2000"))
        print(f"PROPERTY_N={n}")
        rng = random.Random(1337)
        engine = FeeEngineV0()
        for i in range(n):
            payload = {"op": "set", "k": f"k-{i}", "v": rng.randint(0, 10)}
            action = ActionDescriptor(
                kind=ActionKind.STATE_MUTATION,
                module="platform-fee",
                action="mutate",
                payload=payload,
            )
            platform_amount = rng.randint(0, 3)
            payer_a = f"payer-{rng.randint(0, 100)}"
            payer_b = f"payer-{rng.randint(0, 100)}"
            quote_a = quote_platform_fee(engine, action, payer=payer_a, platform_fee_amount=platform_amount)
            quote_b = quote_platform_fee(engine, action, payer=payer_b, platform_fee_amount=platform_amount)
            self.assertEqual(
                quote_a.protocol_quote.fee_vector,
                quote_b.protocol_quote.fee_vector,
            )
            self.assertEqual(quote_a.total_due, quote_b.total_due)
            self.assertEqual(
                quote_a.total_due,
                quote_a.protocol_quote.fee_vector.total() + platform_amount,
            )


if __name__ == "__main__":
    unittest.main()
