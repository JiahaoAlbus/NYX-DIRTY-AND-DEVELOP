import sys
from pathlib import Path
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = REPO_ROOT / "packages" / "l2-private-ledger" / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from l2_private_ledger.actions import ActionKind, LedgerAction, PrivateMint, PrivateSpend  # noqa: E402
from l2_private_ledger.kernel import apply_action  # noqa: E402
from l2_private_ledger.state import empty_state  # noqa: E402


class KernelTests(unittest.TestCase):
    def test_mint_and_spend(self):
        state = empty_state()
        commitment = b"\x01" * 32
        action = LedgerAction(ActionKind.PRIVATE_MINT, PrivateMint(commitment))
        next_state = apply_action(state, action)
        self.assertIn(commitment, next_state.commitments)

        nullifier = b"\x02" * 32
        spend_action = LedgerAction(ActionKind.PRIVATE_SPEND, PrivateSpend(nullifier))
        final_state = apply_action(next_state, spend_action)
        self.assertIn(nullifier, final_state.nullifiers)


if __name__ == "__main__":
    unittest.main()
