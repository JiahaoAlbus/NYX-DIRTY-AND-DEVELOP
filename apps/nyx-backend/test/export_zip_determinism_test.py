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

from nyx_backend.evidence import build_export_zip, run_evidence  # noqa: E402


class ExportZipDeterminismTests(unittest.TestCase):
    def test_export_zip_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp1, tempfile.TemporaryDirectory() as tmp2:
            base1 = Path(tmp1)
            base2 = Path(tmp2)
            run_evidence(
                seed=42,
                run_id="deterministic-run",
                module="exchange",
                action="route_swap",
                payload={"route": "basic"},
                base_dir=base1,
            )
            run_evidence(
                seed=42,
                run_id="deterministic-run",
                module="exchange",
                action="route_swap",
                payload={"route": "basic"},
                base_dir=base2,
            )
            zip1 = build_export_zip("deterministic-run", base_dir=base1)
            zip2 = build_export_zip("deterministic-run", base_dir=base2)
            self.assertEqual(zip1, zip2)


if __name__ == "__main__":
    unittest.main()
