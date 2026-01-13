import sys
from pathlib import Path
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
PL_SRC = REPO_ROOT / "packages" / "l2-private-ledger" / "src"
ZK_SRC = REPO_ROOT / "packages" / "l0-zk-id" / "src"
for path in (PL_SRC, ZK_SRC):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from l2_private_ledger.actions import ActionKind, LedgerAction, PrivateMint, PrivateSpend  # noqa: E402
from l2_private_ledger.kernel import apply_action  # noqa: E402
from l2_private_ledger.proof_wiring import (  # noqa: E402
    DEFAULT_STATEMENT_ID,
    prove_private_action_mock,
    verify_private_action,
)
from l2_private_ledger.state import empty_state, state_root  # noqa: E402
from l2_private_ledger.types import sha256  # noqa: E402


class ProofWiringHappyPathTests(unittest.TestCase):
    def test_mint_and_spend_paths(self):
        state = empty_state()
        commitment = sha256(b"commitment-1")
        mint_action = LedgerAction(ActionKind.PRIVATE_MINT, PrivateMint(commitment))
        nonce = sha256(b"nonce-1")
        envelope = prove_private_action_mock(
            state,
            mint_action,
            nonce,
            witness={"tag": "mint"},
        )
        self.assertTrue(verify_private_action(envelope, state_root(state), mint_action))

        wrong_context = sha256(b"wrong-context")
        self.assertFalse(
            verify_private_action(
                envelope,
                state_root(state),
                mint_action,
                context_id=wrong_context,
            )
        )

        next_state = apply_action(state, mint_action)
        nullifier = sha256(b"nullifier-1")
        spend_action = LedgerAction(ActionKind.PRIVATE_SPEND, PrivateSpend(nullifier))
        nonce2 = sha256(b"nonce-2")
        envelope2 = prove_private_action_mock(
            next_state,
            spend_action,
            nonce2,
            witness={"tag": "spend"},
        )
        self.assertTrue(
            verify_private_action(envelope2, state_root(next_state), spend_action)
        )

        wrong_statement = f"{DEFAULT_STATEMENT_ID}:wrong"
        self.assertFalse(
            verify_private_action(
                envelope2,
                state_root(next_state),
                spend_action,
                statement_id=wrong_statement,
            )
        )


if __name__ == "__main__":
    unittest.main()
