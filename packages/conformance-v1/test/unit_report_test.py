import json
import sys
from pathlib import Path
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = REPO_ROOT / "packages" / "conformance-v1" / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from conformance_v1.model import DrillResult, Report, Rule  # noqa: E402
from conformance_v1.report import report_to_json  # noqa: E402


class ReportTests(unittest.TestCase):
    def test_attack_cards_emitted_on_failure(self):
        rule = Rule(
            rule_id="Q1-TEST-01",
            adversary_class=("External Hackers",),
            attack_vector="tamper replay",
            surface="Protocol Logic",
            severity="HIGH",
            rationale="test rule",
            detection="runtime drill",
            repro_command="python -m conformance_v1.runner",
        )
        report = Report(
            rules=(rule,),
            results=(DrillResult(rule_id="Q1-TEST-01", passed=False, evidence="evidence"),),
        )
        payload = json.loads(report_to_json(report))
        cards = payload["attack_cards"]
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0]["rule_id"], "Q1-TEST-01")
        self.assertEqual(cards[0]["attack_vector"], "tamper replay")
        self.assertEqual(cards[0]["repro_command"], "python -m conformance_v1.runner")


if __name__ == "__main__":
    unittest.main()
