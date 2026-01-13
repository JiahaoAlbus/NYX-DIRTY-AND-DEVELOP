import sys
from pathlib import Path
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = REPO_ROOT / "packages" / "l2-private-ledger" / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from l2_private_ledger.actions import ActionKind, LedgerAction, PrivateMint, PrivateSpend  # noqa: E402
from l2_private_ledger.kernel import run_actions_with_trace  # noqa: E402
from l2_private_ledger.state import empty_state  # noqa: E402
from l2_private_ledger.trace import LedgerTrace, LedgerTraceEntry, replay_and_verify  # noqa: E402
from l2_private_ledger.types import xor_one_bit  # noqa: E402


class TamperReplayTests(unittest.TestCase):
    def test_tamper_commitment_fails(self):
        actions = [
            LedgerAction(ActionKind.PRIVATE_MINT, PrivateMint(b"\x08" * 32)),
            LedgerAction(ActionKind.PRIVATE_SPEND, PrivateSpend(b"\x09" * 32)),
        ]
        state, trace = run_actions_with_trace(empty_state(), actions)
        tampered_action = LedgerAction(
            ActionKind.PRIVATE_MINT,
            PrivateMint(xor_one_bit(actions[0].payload.commitment, 3)),
        )
        tampered_entry = LedgerTraceEntry(action=tampered_action, after_root=trace.entries[0].after_root)
        tampered_trace = LedgerTrace(entries=(tampered_entry,) + trace.entries[1:], final_state=state)
        self.assertFalse(replay_and_verify(empty_state(), tampered_trace))

    def test_tamper_nullifier_fails(self):
        actions = [
            LedgerAction(ActionKind.PRIVATE_MINT, PrivateMint(b"\x0a" * 32)),
            LedgerAction(ActionKind.PRIVATE_SPEND, PrivateSpend(b"\x0b" * 32)),
        ]
        state, trace = run_actions_with_trace(empty_state(), actions)
        tampered_action = LedgerAction(
            ActionKind.PRIVATE_SPEND,
            PrivateSpend(xor_one_bit(actions[1].payload.nullifier, 7)),
        )
        tampered_entry = LedgerTraceEntry(action=tampered_action, after_root=trace.entries[1].after_root)
        tampered_trace = LedgerTrace(entries=(trace.entries[0], tampered_entry), final_state=state)
        self.assertFalse(replay_and_verify(empty_state(), tampered_trace))

    def test_tamper_root_fails(self):
        actions = [
            LedgerAction(ActionKind.PRIVATE_MINT, PrivateMint(b"\x0c" * 32)),
        ]
        state, trace = run_actions_with_trace(empty_state(), actions)
        tampered_root = xor_one_bit(trace.entries[0].after_root, 10)
        tampered_entry = LedgerTraceEntry(action=trace.entries[0].action, after_root=tampered_root)
        tampered_trace = LedgerTrace(entries=(tampered_entry,), final_state=state)
        self.assertFalse(replay_and_verify(empty_state(), tampered_trace))


if __name__ == "__main__":
    unittest.main()
