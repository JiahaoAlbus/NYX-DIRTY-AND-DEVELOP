import sys
from pathlib import Path
import unittest


class CompareDigestGuardTests(unittest.TestCase):
    def test_compare_digest_used_in_replay(self):
        repo_root = Path(__file__).resolve().parents[3]
        trace_path = (
            repo_root
            / "packages"
            / "l2-private-ledger"
            / "src"
            / "l2_private_ledger"
            / "trace.py"
        )
        content = trace_path.read_text(encoding="utf-8")
        self.assertIn("compare_digest(", content)


if __name__ == "__main__":
    unittest.main()
