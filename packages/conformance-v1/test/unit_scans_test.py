import sys
from pathlib import Path
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = REPO_ROOT / "packages" / "conformance-v1" / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from conformance_v1.scans import SCAN_RULES, scan_texts  # noqa: E402


def _join(parts: list[str]) -> str:
    return "".join(parts)


_ID_WORD = _join(["iden", "tity"])


class ScanUnitTests(unittest.TestCase):
    def test_scan_finds_keyword(self):
        text = "address_as_" + _ID_WORD + " = True\n"
        findings = scan_texts([("fixture.py", text)], SCAN_RULES)
        self.assertTrue(findings["Q1-ID-01"])

    def test_scan_findings_empty_for_clean_text(self):
        text = "safe_variable = 1\n"
        findings = scan_texts([("fixture.py", text)], SCAN_RULES)
        for rule_id, matches in findings.items():
            self.assertEqual(matches, [])


if __name__ == "__main__":
    unittest.main()
