import json
import sys
from pathlib import Path
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = REPO_ROOT / "packages" / "conformance-v1" / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from conformance_v1.report import report_to_json  # noqa: E402
from conformance_v1.runner import run_all  # noqa: E402


class ReportSchemaTests(unittest.TestCase):
    def test_report_schema_fields(self):
        report = run_all()
        payload = json.loads(report_to_json(report))
        self.assertIsInstance(payload.get("rules"), list)
        self.assertIsInstance(payload.get("results"), list)
        self.assertIsInstance(payload.get("attack_cards"), list)
        rule_ids = [rule["rule_id"] for rule in payload["rules"]]
        self.assertEqual(len(rule_ids), len(set(rule_ids)))
        for rule in payload["rules"]:
            for key in (
                "rule_id",
                "adversary_class",
                "attack_vector",
                "surface",
                "severity",
                "rationale",
                "detection",
                "repro_command",
            ):
                self.assertIn(key, rule)


if __name__ == "__main__":
    unittest.main()
