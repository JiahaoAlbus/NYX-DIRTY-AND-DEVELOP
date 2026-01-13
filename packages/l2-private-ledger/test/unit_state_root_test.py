import sys
from pathlib import Path
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = REPO_ROOT / "packages" / "l2-private-ledger" / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from l2_private_ledger.actions import ActionKind, LedgerAction, PrivateMint, PrivateSpend  # noqa: E402
from l2_private_ledger.kernel import apply_action  # noqa: E402
from l2_private_ledger.state import empty_state, recompute_root, state_root  # noqa: E402
from l2_private_ledger.types import compare_digest  # noqa: E402


class StateRootTests(unittest.TestCase):
    def test_root_recompute(self):
        state = empty_state()
        root_a = state_root(state)
        root_b = recompute_root(state)
        self.assertTrue(compare_digest(root_a, root_b))

    def test_root_changes(self):
        state = empty_state()
        root_a = state_root(state)
        state = apply_action(state, LedgerAction(ActionKind.PRIVATE_MINT, PrivateMint(b"\x03" * 32)))
        root_b = state_root(state)
        self.assertFalse(compare_digest(root_a, root_b))

    def test_order_independent(self):
        actions = [
            LedgerAction(ActionKind.PRIVATE_MINT, PrivateMint(b"\x04" * 32)),
            LedgerAction(ActionKind.PRIVATE_MINT, PrivateMint(b"\x05" * 32)),
            LedgerAction(ActionKind.PRIVATE_SPEND, PrivateSpend(b"\x06" * 32)),
        ]
        state_a = empty_state()
        for action in actions:
            state_a = apply_action(state_a, action)
        state_b = empty_state()
        for action in reversed(actions):
            state_b = apply_action(state_b, action)
        root_a = state_root(state_a)
        root_b = state_root(state_b)
        self.assertEqual(state_a.commitments, state_b.commitments)
        self.assertEqual(state_a.nullifiers, state_b.nullifiers)
        self.assertTrue(compare_digest(root_a, root_b))


if __name__ == "__main__":
    unittest.main()
