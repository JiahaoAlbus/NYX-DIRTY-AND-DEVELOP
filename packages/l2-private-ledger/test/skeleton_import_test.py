import sys
from pathlib import Path
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = REPO_ROOT / "packages" / "l2-private-ledger" / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from l2_private_ledger import (  # noqa: E402
    Commitment,
    LedgerRoot,
    Note,
    Nullifier,
    PrivateLedgerKernel,
)


class SkeletonImportTests(unittest.TestCase):
    def test_types_and_interfaces_exist(self):
        self.assertTrue(Commitment)
        self.assertTrue(LedgerRoot)
        self.assertTrue(Note)
        self.assertTrue(Nullifier)
        self.assertTrue(PrivateLedgerKernel)


if __name__ == "__main__":
    unittest.main()
