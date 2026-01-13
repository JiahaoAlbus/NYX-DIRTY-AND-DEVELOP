import sys
from pathlib import Path
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = REPO_ROOT / "packages" / "conformance-v1" / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from conformance_v1.ruleset import RULES  # noqa: E402


class RulesetNonDilutionTests(unittest.TestCase):
    def test_ruleset_baseline(self):
        baseline_ids = {
            "Q1-ID-01",
            "Q1-ID-02",
            "Q1-FEE-01",
            "Q1-FEE-02",
            "Q1-ZK-01",
            "Q1-ZK-02",
            "Q1-SECRET-01",
            "Q1-TRACE-01",
            "Q1-TRACE-02",
            "Q1-TRACE-03",
            "Q1-PRIV-01",
            "Q1-PLAT-01",
            "Q1-ANALYTICS-01",
        }
        ids = {rule.rule_id for rule in RULES}
        self.assertTrue(baseline_ids.issubset(ids))
        self.assertGreaterEqual(len(ids), len(baseline_ids))


if __name__ == "__main__":
    unittest.main()
