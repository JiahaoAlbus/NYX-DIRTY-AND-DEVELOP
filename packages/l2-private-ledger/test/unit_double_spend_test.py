import sys
from pathlib import Path
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = REPO_ROOT / "packages" / "l2-private-ledger" / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from l2_private_ledger.actions import ActionKind, LedgerAction, PrivateSpend  # noqa: E402
from l2_private_ledger.errors import DoubleSpendError  # noqa: E402
from l2_private_ledger.kernel import apply_action  # noqa: E402
from l2_private_ledger.state import empty_state  # noqa: E402


class DoubleSpendTests(unittest.TestCase):
    def test_double_spend_fails(self):
        state = empty_state()
        nullifier = b"\x07" * 32
        spend = LedgerAction(ActionKind.PRIVATE_SPEND, PrivateSpend(nullifier))
        state = apply_action(state, spend)
        with self.assertRaises(DoubleSpendError):
            apply_action(state, spend)


if __name__ == "__main__":
    unittest.main()
