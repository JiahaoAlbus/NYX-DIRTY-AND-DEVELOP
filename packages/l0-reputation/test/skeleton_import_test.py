import sys
from pathlib import Path
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = REPO_ROOT / "packages" / "l0-reputation" / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from l0_reputation import (  # noqa: E402
    DisclosureStatement,
    PseudonymId,
    RepEvent,
    RepEventId,
    RepRoot,
    ReputationKernel,
)


class SkeletonImportTests(unittest.TestCase):
    def test_types_and_interfaces_exist(self):
        self.assertTrue(PseudonymId)
        self.assertTrue(RepRoot)
        self.assertTrue(RepEventId)
        self.assertTrue(RepEvent)
        self.assertTrue(DisclosureStatement)
        self.assertTrue(ReputationKernel)


if __name__ == "__main__":
    unittest.main()
