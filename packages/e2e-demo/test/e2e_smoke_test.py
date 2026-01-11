import os
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PATHS = [
    REPO_ROOT / "packages" / "e2e-demo" / "src",
    REPO_ROOT / "packages" / "l0-zk-id" / "src",
    REPO_ROOT / "packages" / "l2-economics" / "src",
    REPO_ROOT / "packages" / "l1-chain" / "src",
    REPO_ROOT / "packages" / "wallet-kernel" / "src",
]
for path in PATHS:
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from e2e_demo.hashing import compare_digest  # noqa: E402
from e2e_demo.pipeline import run_e2e  # noqa: E402
from e2e_demo.replay import replay_and_verify  # noqa: E402


class E2ESmokeTests(unittest.TestCase):
    def test_e2e_pipeline(self):
        trace, summary = run_e2e(seed=123)
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(trace.to_json().encode("utf-8"))
            tmp_path = tmp.name
        try:
            result = replay_and_verify(trace)
            self.assertTrue(result.ok)
            self.assertGreater(summary.fee_total, 0)
            self.assertFalse(
                compare_digest(
                    bytes.fromhex(trace.chain.state_root_before_hex),
                    bytes.fromhex(trace.chain.state_root_after_hex),
                )
            )
            self.assertFalse(trace.sanity.wrong_context_verified)
            self.assertTrue(trace.sanity.correct_context_verified)
        finally:
            os.unlink(tmp_path)


if __name__ == "__main__":
    unittest.main()
