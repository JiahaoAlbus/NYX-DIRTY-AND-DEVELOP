import tempfile
import unittest
from pathlib import Path
import sys


BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parents[1]
SRC = BACKEND_ROOT / "src"
PKG_PATHS = [
    SRC,
    REPO_ROOT / "packages" / "e2e-private-transfer" / "src",
    REPO_ROOT / "packages" / "l2-private-ledger" / "src",
    REPO_ROOT / "packages" / "l0-zk-id" / "src",
    REPO_ROOT / "packages" / "l2-economics" / "src",
    REPO_ROOT / "packages" / "l1-chain" / "src",
    REPO_ROOT / "packages" / "wallet-kernel" / "src",
]
for path in PKG_PATHS:
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from nyx_backend.evidence import load_evidence, run_evidence  # noqa: E402


class EvidenceFlowTests(unittest.TestCase):
    def test_evidence_flow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = Path(tmp)
            payload = run_evidence(
                seed=123,
                run_id="demo-run",
                module="exchange",
                action="route_swap",
                payload={"route": "basic"},
                base_dir=base_dir,
            )
            loaded = load_evidence("demo-run", base_dir=base_dir)
            self.assertEqual(payload.state_hash, loaded.state_hash)
            self.assertTrue(payload.replay_ok)


if __name__ == "__main__":
    unittest.main()
