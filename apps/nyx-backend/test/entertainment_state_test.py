import tempfile
import unittest
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
PKG_PATHS = [
    SRC,
    ROOT.parents[1] / "packages" / "e2e-private-transfer" / "src",
    ROOT.parents[1] / "packages" / "l2-private-ledger" / "src",
    ROOT.parents[1] / "packages" / "l0-zk-id" / "src",
    ROOT.parents[1] / "packages" / "l2-economics" / "src",
    ROOT.parents[1] / "packages" / "l2-platform-fee" / "src",
    ROOT.parents[1] / "packages" / "l1-chain" / "src",
    ROOT.parents[1] / "packages" / "wallet-kernel" / "src",
]
for path in PKG_PATHS:
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from nyx_backend.evidence import EvidenceError, run_evidence  # noqa: E402


class EntertainmentStateTests(unittest.TestCase):
    def test_entertainment_state_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = Path(tmp)
            payload = run_evidence(
                seed=123,
                run_id="ent-123",
                module="entertainment",
                action="state_step",
                payload={"mode": "pulse", "step": 1},
                base_dir=base_dir,
            )
            state = payload.outputs.get("entertainment_state")
            self.assertIsInstance(state, dict)
            self.assertEqual(state.get("mode"), "pulse")
            self.assertEqual(state.get("step"), 1)
            self.assertTrue(state.get("state_hash"))

    def test_entertainment_state_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = Path(tmp)
            payload_a = run_evidence(
                seed=123,
                run_id="ent-abc",
                module="entertainment",
                action="state_step",
                payload={"mode": "orbit", "step": 2},
                base_dir=base_dir,
            )
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = Path(tmp)
            payload_b = run_evidence(
                seed=123,
                run_id="ent-def",
                module="entertainment",
                action="state_step",
                payload={"mode": "orbit", "step": 2},
                base_dir=base_dir,
            )
        self.assertEqual(
            payload_a.outputs["entertainment_state"]["state_hash"],
            payload_b.outputs["entertainment_state"]["state_hash"],
        )

    def test_entertainment_invalid_step_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = Path(tmp)
            with self.assertRaises(EvidenceError):
                run_evidence(
                    seed=123,
                    run_id="ent-bad",
                    module="entertainment",
                    action="state_step",
                    payload={"mode": "pulse", "step": 99},
                    base_dir=base_dir,
                )


if __name__ == "__main__":
    unittest.main()
