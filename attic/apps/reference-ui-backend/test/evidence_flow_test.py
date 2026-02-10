import tempfile
from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
PATHS = [
    REPO_ROOT / "apps" / "reference-ui-backend" / "src",
    REPO_ROOT / "packages" / "e2e-private-transfer" / "src",
    REPO_ROOT / "packages" / "l2-private-ledger" / "src",
    REPO_ROOT / "packages" / "l0-zk-id" / "src",
    REPO_ROOT / "packages" / "l2-economics" / "src",
    REPO_ROOT / "packages" / "l1-chain" / "src",
    REPO_ROOT / "packages" / "wallet-kernel" / "src",
]
for path in PATHS:
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from nyx_reference_ui_backend.evidence import load_evidence, run_evidence  # noqa: E402


class EvidenceFlowTests(unittest.TestCase):
    def test_evidence_flow(self):
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = Path(tmp)
            run_evidence(seed=123, run_id="seed-123", base_dir=base_dir)
            payload = load_evidence("seed-123", base_dir)
            self.assertTrue(payload.replay_ok)
            self.assertTrue(payload.state_hash)
            self.assertTrue(payload.receipt_hashes)


if __name__ == "__main__":
    unittest.main()
