import os
import random
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
    DEFAULT_CONTEXT_ID,
    prove_private_action_mock,
    verify_private_action,
)
from l2_private_ledger.state import empty_state, state_root  # noqa: E402
from l2_private_ledger.types import compare_digest, sha256  # noqa: E402


class ContextStatementPropertyTests(unittest.TestCase):
    def test_context_statement_separation(self):
        n = int(os.getenv("PROPERTY_N", "2000"))
        print(f"PROPERTY_N={n}")
        rng = random.Random(4142)
        for _ in range(n):
            state = empty_state()
            commitments: set[bytes] = set()
            nullifiers: set[bytes] = set()
            for _ in range(rng.randint(0, 5)):
                if rng.random() < 0.5:
                    seed = rng.getrandbits(256).to_bytes(32, "big")
                    commitment = sha256(b"c" + seed)
                    if commitment in commitments:
                        continue
                    commitments.add(commitment)
                    state = apply_action(
                        state, LedgerAction(ActionKind.PRIVATE_MINT, PrivateMint(commitment))
                    )
                else:
                    seed = rng.getrandbits(256).to_bytes(32, "big")
                    nullifier = sha256(b"n" + seed)
                    if nullifier in nullifiers:
                        continue
                    nullifiers.add(nullifier)
                    state = apply_action(
                        state, LedgerAction(ActionKind.PRIVATE_SPEND, PrivateSpend(nullifier))
                    )

            if rng.random() < 0.5:
                commitment = sha256(b"ac" + rng.getrandbits(256).to_bytes(32, "big"))
                action = LedgerAction(ActionKind.PRIVATE_MINT, PrivateMint(commitment))
            else:
                nullifier = sha256(b"an" + rng.getrandbits(256).to_bytes(32, "big"))
                action = LedgerAction(ActionKind.PRIVATE_SPEND, PrivateSpend(nullifier))

            nonce = sha256(rng.getrandbits(256).to_bytes(32, "big"))
            envelope = prove_private_action_mock(
                state,
                action,
                nonce,
                witness={"seed": rng.getrandbits(32)},
            )
            expected_root = state_root(state)
            self.assertTrue(verify_private_action(envelope, expected_root, action))

            attempts = 0
            checked = 0
            while checked < 10 and attempts < 30:
                attempts += 1
                wrong_context = sha256(
                    b"wrong" + rng.getrandbits(256).to_bytes(32, "big")
                )
                if compare_digest(wrong_context, DEFAULT_CONTEXT_ID):
                    continue
                checked += 1
                self.assertFalse(
                    verify_private_action(
                        envelope,
                        expected_root,
                        action,
                        context_id=wrong_context,
                    )
                )
            self.assertEqual(checked, 10)

            for idx in range(3):
                wrong_statement = f"{DEFAULT_STATEMENT_ID}:alt:{idx}"
                self.assertFalse(
                    verify_private_action(
                        envelope,
                        expected_root,
                        action,
                        statement_id=wrong_statement,
                    )
                )


if __name__ == "__main__":
    unittest.main()
