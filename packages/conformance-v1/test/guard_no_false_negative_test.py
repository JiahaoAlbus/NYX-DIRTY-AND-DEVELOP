import sys
from pathlib import Path
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = REPO_ROOT / "packages" / "conformance-v1" / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from conformance_v1.scans import SCAN_RULES, scan_texts  # noqa: E402


class GuardNoFalseNegativeTests(unittest.TestCase):
    def test_each_rule_matches_fixture(self):
        hex64 = "a" * 64
        fixtures = [
            ("id.py", "address_as_identity = 1"),
            ("priv.py", "allowlist = True"),
            ("plat.py", "kyc = True"),
            ("analytics.py", f"acct:{hex64}"),
        ]
        findings = scan_texts(fixtures, SCAN_RULES)
        for rule_id in ("Q1-ID-01", "Q1-PRIV-01", "Q1-PLAT-01", "Q1-ANALYTICS-01"):
            self.assertTrue(findings[rule_id], msg=f"missing detection for {rule_id}")


if __name__ == "__main__":
    unittest.main()
