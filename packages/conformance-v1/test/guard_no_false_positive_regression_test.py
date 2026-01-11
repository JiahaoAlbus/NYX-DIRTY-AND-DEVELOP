import sys
from pathlib import Path
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = REPO_ROOT / "packages" / "conformance-v1" / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from conformance_v1.scans import SCAN_RULES, scan_texts  # noqa: E402


class GuardNoFalsePositiveTests(unittest.TestCase):
    def test_split_tokens_do_not_match(self):
        fixtures = [
            ("split_id.py", "address_as\nidentity"),
            ("split_priv.py", "allow\nlist"),
            ("word_boundary.py", "skyc = True"),
            ("analytics_short.py", "acct:" + "b" * 63),
        ]
        findings = scan_texts(fixtures, SCAN_RULES)
        for rule_id, matches in findings.items():
            self.assertEqual(matches, [], msg=f"false positive for {rule_id}")


if __name__ == "__main__":
    unittest.main()
