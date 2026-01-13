import os
import random
import sys
from pathlib import Path
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = REPO_ROOT / "packages" / "l2-private-ledger" / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from l2_private_ledger.actions import ActionKind, LedgerAction, PrivateMint, PrivateSpend  # noqa: E402
from l2_private_ledger.kernel import run_actions_with_trace  # noqa: E402
from l2_private_ledger.state import empty_state, recompute_root, state_root  # noqa: E402
from l2_private_ledger.trace import LedgerTrace, LedgerTraceEntry, replay_and_verify  # noqa: E402
from l2_private_ledger.types import compare_digest, sha256, xor_one_bit  # noqa: E402


class PrivateLedgerPropertyTests(unittest.TestCase):
    def test_property_invariants(self):
        n = int(os.getenv("PROPERTY_N", "2000"))
        print(f"PROPERTY_N={n}")
        rng = random.Random(1337)
        for _ in range(n):
            length = rng.randint(8, 20)
            commitments = set()
            nullifiers = set()
            actions: list[LedgerAction] = []
            while len(actions) < length:
                if rng.random() < 0.5:
                    seed = rng.getrandbits(256).to_bytes(32, "big")
                    commitment = sha256(b"c" + seed)
                    if commitment in commitments:
                        continue
                    commitments.add(commitment)
                    actions.append(
                        LedgerAction(ActionKind.PRIVATE_MINT, PrivateMint(commitment))
                    )
                else:
                    seed = rng.getrandbits(256).to_bytes(32, "big")
                    nullifier = sha256(b"n" + seed)
                    if nullifier in nullifiers:
                        continue
                    nullifiers.add(nullifier)
                    actions.append(
                        LedgerAction(ActionKind.PRIVATE_SPEND, PrivateSpend(nullifier))
                    )

            state_a, trace_a = run_actions_with_trace(empty_state(), actions)
            self.assertTrue(replay_and_verify(empty_state(), trace_a))
            root_a = state_root(state_a)
            self.assertTrue(compare_digest(root_a, recompute_root(state_a)))

            shuffled = list(actions)
            rng.shuffle(shuffled)
            state_b, trace_b = run_actions_with_trace(empty_state(), shuffled)
            root_b = state_root(state_b)
            self.assertEqual(state_a.commitments, state_b.commitments)
            self.assertEqual(state_a.nullifiers, state_b.nullifiers)
            self.assertTrue(compare_digest(root_a, root_b))
            self.assertTrue(replay_and_verify(empty_state(), trace_b))

            entry = trace_a.entries[rng.randrange(len(trace_a.entries))]
            if entry.action.kind == ActionKind.PRIVATE_MINT:
                mutated = LedgerAction(
                    ActionKind.PRIVATE_MINT,
                    PrivateMint(xor_one_bit(entry.action.payload.commitment, 1)),
                )
            else:
                mutated = LedgerAction(
                    ActionKind.PRIVATE_SPEND,
                    PrivateSpend(xor_one_bit(entry.action.payload.nullifier, 1)),
                )
            tampered_entry = LedgerTraceEntry(action=mutated, after_root=entry.after_root)
            tampered_entries = tuple(
                tampered_entry if e is entry else e for e in trace_a.entries
            )
            tampered_trace = LedgerTrace(entries=tampered_entries, final_state=state_a)
            self.assertFalse(replay_and_verify(empty_state(), tampered_trace))


if __name__ == "__main__":
    unittest.main()
