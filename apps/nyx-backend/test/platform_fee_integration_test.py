import tempfile
import unittest
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
PKG_PATHS = [
    SRC,
    ROOT.parents[1] / "packages" / "e2e-private-transfer" / "src",
    ROOT.parents[1] / "packages" / "l2-private-ledger" / "src",
    ROOT.parents[1] / "packages" / "l0-zk-id" / "src",
    ROOT.parents[1] / "packages" / "l2-economics" / "src",
    ROOT.parents[1] / "packages" / "l2-platform-fee" / "src",
    ROOT.parents[1] / "packages" / "l1-chain" / "src",
    ROOT.parents[1] / "packages" / "wallet-kernel" / "src",
]
for path in PKG_PATHS:
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from nyx_backend.evidence import run_evidence  # noqa: E402


class PlatformFeeIntegrationTests(unittest.TestCase):
    def test_marketplace_platform_fee_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = Path(tmp)
            payload = run_evidence(
                seed=123,
                run_id="market-123",
                module="marketplace",
                action="order_intent",
                payload={"item_id": "kit-01", "quantity": 1},
                base_dir=base_dir,
            )
            outputs = payload.outputs
            self.assertIn("platform_fee", outputs)
            platform_fee = outputs["platform_fee"]
            self.assertEqual(platform_fee.get("platform_fee_amount"), 1)
            protocol_total = platform_fee.get("protocol_fee_total")
            total_due = platform_fee.get("total_due")
            total_paid = platform_fee.get("total_paid")
            self.assertIsInstance(protocol_total, int)
            self.assertGreater(protocol_total, 0)
            self.assertEqual(total_due, protocol_total + platform_fee.get("platform_fee_amount"))
            self.assertEqual(total_paid, total_due)

    def test_non_marketplace_has_no_platform_fee(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = Path(tmp)
            payload = run_evidence(
                seed=123,
                run_id="exchange-123",
                module="exchange",
                action="route_swap",
                payload={"route": "basic"},
                base_dir=base_dir,
            )
            self.assertNotIn("platform_fee", payload.outputs)


if __name__ == "__main__":
    unittest.main()
