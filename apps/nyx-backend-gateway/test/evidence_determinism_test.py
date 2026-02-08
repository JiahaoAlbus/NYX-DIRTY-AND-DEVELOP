import json
import sys
import tempfile
import unittest
from pathlib import Path

import _bootstrap  # noqa: F401

_BACKEND_SRC = Path(__file__).resolve().parents[2] / "nyx-backend" / "src"
if str(_BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(_BACKEND_SRC))

from nyx_backend.evidence import run_evidence  # noqa: E402


def _find_run_dir(run_root: Path, run_id: str) -> Path:
    for entry in run_root.iterdir():
        if not entry.is_dir():
            continue
        run_id_path = entry / "run_id.txt"
        if run_id_path.exists() and run_id_path.read_text(encoding="utf-8").strip() == run_id:
            return entry
    raise AssertionError("run directory not found")


class EvidenceDeterminismTests(unittest.TestCase):
    def test_exchange_evidence_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_root = Path(tmp) / "runs"
            payload = {
                "asset_in": "asset-a",
                "asset_out": "asset-b",
                "amount": 5,
                "min_out": 3,
            }
            first = run_evidence(
                seed=123,
                run_id="run-a",
                module="exchange",
                action="route_swap",
                payload=payload,
                base_dir=run_root,
            )
            second = run_evidence(
                seed=123,
                run_id="run-b",
                module="exchange",
                action="route_swap",
                payload=payload,
                base_dir=run_root,
            )
            self.assertEqual(first.state_hash, second.state_hash)
            self.assertEqual(first.receipt_hashes, second.receipt_hashes)
            first_dir = _find_run_dir(run_root, "run-a")
            second_dir = _find_run_dir(run_root, "run-b")
            first_json = json.loads((first_dir / "evidence.json").read_text(encoding="utf-8"))
            second_json = json.loads((second_dir / "evidence.json").read_text(encoding="utf-8"))
            self.assertEqual(first_json, second_json)

    def test_wallet_transfer_evidence_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_root = Path(tmp) / "runs"
            payload = {
                "from_address": "acct-alpha",
                "to_address": "acct-beta",
                "amount": 5,
                "asset_id": "NYXT",
            }
            first = run_evidence(
                seed=123,
                run_id="run-w1",
                module="wallet",
                action="transfer",
                payload=payload,
                base_dir=run_root,
            )
            second = run_evidence(
                seed=123,
                run_id="run-w2",
                module="wallet",
                action="transfer",
                payload=payload,
                base_dir=run_root,
            )
            self.assertEqual(first.state_hash, second.state_hash)
            self.assertEqual(first.receipt_hashes, second.receipt_hashes)


if __name__ == "__main__":
    unittest.main()
