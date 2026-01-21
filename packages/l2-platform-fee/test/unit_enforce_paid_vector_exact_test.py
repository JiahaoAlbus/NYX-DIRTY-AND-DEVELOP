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
from fee import FeeComponentId, FeeVector  # noqa: E402
from l2_platform_fee.fee_hook import enforce_platform_fee, quote_platform_fee  # noqa: E402
from l2_platform_fee.errors import PlatformFeeError  # noqa: E402


class EnforcePaidVectorExactTests(unittest.TestCase):
    def test_paid_vector_must_match(self):
        action = ActionDescriptor(
            kind=ActionKind.STATE_MUTATION,
            module="platform-fee",
            action="mutate",
            payload={"op": "set", "k": "a", "v": "b"},
        )
        engine = FeeEngineV0()
        quote = quote_platform_fee(engine, action, payer="payer", platform_fee_amount=1)
        bad_vector = FeeVector.for_action(
            ActionKind.STATE_MUTATION,
            (
                (FeeComponentId.BASE, 1),
                (FeeComponentId.BYTES, 0),
                (FeeComponentId.COMPUTE, 0),
            ),
        )
        with self.assertRaises(PlatformFeeError):
            enforce_platform_fee(
                engine,
                quote,
                paid_protocol_vector=bad_vector,
                paid_platform_amount=1,
                payer="payer",
            )
        with self.assertRaises(PlatformFeeError):
            enforce_platform_fee(
                engine,
                quote,
                paid_protocol_vector=quote.protocol_quote.fee_vector,
                paid_platform_amount=0,
                payer="payer",
            )


if __name__ == "__main__":
    unittest.main()
