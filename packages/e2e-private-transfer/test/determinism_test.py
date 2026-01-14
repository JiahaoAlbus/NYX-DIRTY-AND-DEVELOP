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


class DeterminismTests(unittest.TestCase):
    def test_same_seed_same_prefixes(self):
        trace_a, summary_a = run_private_transfer(seed=123)
        trace_b, summary_b = run_private_transfer(seed=123)
        self.assertEqual(summary_a.tx_hash_prefix, summary_b.tx_hash_prefix)
        self.assertEqual(summary_a.block_hash_prefix, summary_b.block_hash_prefix)
        self.assertEqual(summary_a.state_root_prefix, summary_b.state_root_prefix)
        self.assertEqual(summary_a.receipt_hash_prefix, summary_b.receipt_hash_prefix)
        self.assertEqual(summary_a.fee_total, summary_b.fee_total)
        self.assertEqual(trace_a.sanity.wrong_context_failed, trace_b.sanity.wrong_context_failed)


if __name__ == "__main__":
    unittest.main()
