import sys
from pathlib import Path
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = REPO_ROOT / "packages" / "l2-private-ledger" / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from l2_private_ledger.state import LedgerState, state_root  # noqa: E402
from l2_private_ledger.types import sha256  # noqa: E402


class FramingGuardTests(unittest.TestCase):
    def test_root_not_naive_join(self):
        commitment = sha256(b"commitment")
        nullifier = sha256(b"nullifier")
        state = LedgerState(commitments=frozenset({commitment}), nullifiers=frozenset({nullifier}))
        root = state_root(state)
        naive = sha256(b"NYX:PL:ROOT:v0" + commitment + nullifier)
        self.assertNotEqual(root, naive)


if __name__ == "__main__":
    unittest.main()
