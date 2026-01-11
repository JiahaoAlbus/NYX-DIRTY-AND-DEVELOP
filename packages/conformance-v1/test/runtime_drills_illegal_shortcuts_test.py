import sys
from pathlib import Path
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = REPO_ROOT / "packages" / "conformance-v1" / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from conformance_v1.drills import run_drills  # noqa: E402


class RuntimeDrillTests(unittest.TestCase):
    def test_drills_pass(self):
        results = run_drills()
        failures = [result for result in results if not result.passed]
        self.assertEqual(failures, [])


if __name__ == "__main__":
    unittest.main()
