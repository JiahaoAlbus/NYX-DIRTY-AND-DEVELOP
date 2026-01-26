import os
import tempfile
import unittest
from pathlib import Path
import sys


BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parents[1]
SRC = BACKEND_ROOT / "src"
PKG_PATHS = [
    SRC,
    REPO_ROOT / "packages" / "e2e-private-transfer" / "src",
    REPO_ROOT / "packages" / "l2-private-ledger" / "src",
    REPO_ROOT / "packages" / "l0-zk-id" / "src",
    REPO_ROOT / "packages" / "l2-economics" / "src",
    REPO_ROOT / "packages" / "l2-platform-fee" / "src",
    REPO_ROOT / "packages" / "l1-chain" / "src",
    REPO_ROOT / "packages" / "wallet-kernel" / "src",
]
for path in PKG_PATHS:
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from nyx_backend.evidence import run_evidence  # noqa: E402


class FeeSummaryOutputsTests(unittest.TestCase):
    def setUp(self) -> None:
        os.environ.setdefault("NYX_TESTNET_TREASURY_ADDRESS", "treasury-testnet")

    def test_exchange_fee_summary_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = Path(tmp)
            payload = run_evidence(
                seed=123,
                run_id="fee-exchange-1",
                module="exchange",
                action="route_swap",
                payload={"route": "basic"},
                base_dir=base_dir,
            )
            outputs = payload.outputs
            self.assertIn("fee_total", outputs)
            self.assertIn("fee_breakdown", outputs)
            self.assertIn("treasury_address", outputs)
            self.assertGreater(outputs.get("fee_total", 0), 0)

    def test_wallet_transfer_fee_summary_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = Path(tmp)
            payload = run_evidence(
                seed=123,
                run_id="fee-wallet-1",
                module="wallet",
                action="transfer",
                payload={"from_address": "wallet-a", "to_address": "wallet-b", "amount": 5},
                base_dir=base_dir,
            )
            outputs = payload.outputs
            self.assertIn("fee_total", outputs)
            self.assertIn("fee_breakdown", outputs)
            self.assertIn("treasury_address", outputs)
            self.assertGreater(outputs.get("fee_total", 0), 0)


if __name__ == "__main__":
    unittest.main()
