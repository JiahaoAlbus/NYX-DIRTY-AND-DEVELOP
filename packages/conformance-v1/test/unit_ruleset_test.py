import sys
from pathlib import Path
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = REPO_ROOT / "packages" / "conformance-v1" / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from conformance_v1.ruleset import (  # noqa: E402
    ADVERSARY_CLASSES,
    DETECTION_BOTH,
    DETECTION_RUNTIME,
    DETECTION_STATIC,
    RULES,
)


class RuleSetTests(unittest.TestCase):
    def test_rules_unique(self):
        ids = [rule.rule_id for rule in RULES]
        self.assertEqual(len(ids), len(set(ids)))

    def test_rules_complete(self):
        expected_ids = {
            "Q1-ID-01",
            "Q1-ID-02",
            "Q1-FEE-01",
            "Q1-FEE-02",
            "Q7-FEE-PLAT-01",
            "Q1-ZK-01",
            "Q1-ZK-02",
            "Q1-SECRET-01",
            "Q1-TRACE-01",
            "Q1-TRACE-02",
            "Q1-TRACE-03",
            "Q1-PRIV-01",
            "Q1-PLAT-01",
            "Q1-ANALYTICS-01",
            "Q5-ROUTER-01",
            "Q5-ROUTER-02",
            "Q5-ROUTER-03",
            "Q5-ROUTER-04",
            "Q5-CLIENT-01",
            "Q5-OPS-01",
            "Q7-OUTPUT-01",
        }
        self.assertEqual(expected_ids, {rule.rule_id for rule in RULES})

    def test_rules_fields(self):
        detections = {DETECTION_STATIC, DETECTION_RUNTIME, DETECTION_BOTH}
        for rule in RULES:
            self.assertTrue(rule.rule_id)
            self.assertTrue(rule.attack_vector)
            self.assertTrue(rule.surface)
            self.assertTrue(rule.severity)
            self.assertTrue(rule.rationale)
            self.assertIn(rule.detection, detections)
            self.assertTrue(rule.repro_command)
            for adversary in rule.adversary_class:
                self.assertIn(adversary, ADVERSARY_CLASSES)


if __name__ == "__main__":
    unittest.main()
