import sys
from pathlib import Path
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = REPO_ROOT / "packages" / "e2e-private-transfer" / "src"
PL_SRC = REPO_ROOT / "packages" / "l2-private-ledger" / "src"
ZK_SRC = REPO_ROOT / "packages" / "l0-zk-id" / "src"
ECON_SRC = REPO_ROOT / "packages" / "l2-economics" / "src"
CHAIN_SRC = REPO_ROOT / "packages" / "l1-chain" / "src"
KERNEL_SRC = REPO_ROOT / "packages" / "wallet-kernel" / "src"
for path in (SRC_DIR, PL_SRC, ZK_SRC, ECON_SRC, CHAIN_SRC, KERNEL_SRC):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from e2e_private_transfer.pipeline import run_private_transfer  # noqa: E402
from e2e_private_transfer.replay import replay_and_verify  # noqa: E402


class E2ESmokeTests(unittest.TestCase):
    def test_private_transfer_e2e(self):
        trace, summary = run_private_transfer(seed=123)
        self.assertGreater(summary.fee_total, 0)
        self.assertTrue(trace.sanity.wrong_context_failed)
        self.assertTrue(replay_and_verify(trace))


if __name__ == "__main__":
    unittest.main()
