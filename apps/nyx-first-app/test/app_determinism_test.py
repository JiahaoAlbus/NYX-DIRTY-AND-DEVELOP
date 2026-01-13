import os
import sys
import tempfile
from pathlib import Path
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
PATHS = [
    REPO_ROOT / "apps" / "nyx-first-app" / "src",
    REPO_ROOT / "packages" / "l0-identity" / "src",
    REPO_ROOT / "packages" / "l0-zk-id" / "src",
    REPO_ROOT / "packages" / "l2-economics" / "src",
    REPO_ROOT / "packages" / "l1-chain" / "src",
    REPO_ROOT / "packages" / "wallet-kernel" / "src",
    REPO_ROOT / "packages" / "e2e-demo" / "src",
]
for path in PATHS:
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from nyx_first_app.app import run_app  # noqa: E402


class AppDeterminismTests(unittest.TestCase):
    def test_same_seed_same_prefixes(self):
        fd_a, out_a = tempfile.mkstemp(prefix="nyx_app_a_", suffix=".json")
        os.close(fd_a)
        fd_b, out_b = tempfile.mkstemp(prefix="nyx_app_b_", suffix=".json")
        os.close(fd_b)
        try:
            summary_a = run_app(seed=123, out_path=out_a)
            summary_b = run_app(seed=123, out_path=out_b)
            self.assertEqual(summary_a.tx_hash_prefix, summary_b.tx_hash_prefix)
            self.assertEqual(summary_a.block_hash_prefix, summary_b.block_hash_prefix)
            self.assertEqual(summary_a.state_root_prefix, summary_b.state_root_prefix)
            self.assertEqual(summary_a.receipt_hash_prefix, summary_b.receipt_hash_prefix)
        finally:
            for path in (out_a, out_b):
                try:
                    os.unlink(path)
                except OSError:
                    pass


if __name__ == "__main__":
    unittest.main()
