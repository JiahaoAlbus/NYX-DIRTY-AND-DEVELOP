import sys
from pathlib import Path
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = REPO_ROOT / "packages" / "l2-private-ledger" / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from l2_private_ledger import (  # noqa: E402
    ActionKind,
    Commitment,
    LedgerAction,
    LedgerState,
    LedgerTrace,
    LedgerTraceEntry,
    LedgerRoot,
    Note,
    Nullifier,
    PrivateLedgerKernel,
    PrivateMint,
    PrivateSpend,
    apply_action,
    replay_and_verify,
    state_root,
)


class SkeletonImportTests(unittest.TestCase):
    def test_types_and_interfaces_exist(self):
        self.assertTrue(ActionKind)
        self.assertTrue(Commitment)
        self.assertTrue(LedgerRoot)
        self.assertTrue(Note)
        self.assertTrue(Nullifier)
        self.assertTrue(PrivateMint)
        self.assertTrue(PrivateSpend)
        self.assertTrue(LedgerAction)
        self.assertTrue(LedgerState)
        self.assertTrue(LedgerTraceEntry)
        self.assertTrue(LedgerTrace)
        self.assertTrue(apply_action)
        self.assertTrue(replay_and_verify)
        self.assertTrue(state_root)
        self.assertTrue(PrivateLedgerKernel)


if __name__ == "__main__":
    unittest.main()
