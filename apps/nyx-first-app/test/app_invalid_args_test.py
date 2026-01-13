import sys
from pathlib import Path
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
PATHS = [
    REPO_ROOT / "apps" / "nyx-first-app" / "src",
    REPO_ROOT / "packages" / "l0-identity" / "src",
    REPO_ROOT / "packages" / "l0-zk-id" / "src",
    REPO_ROOT / "packages" / "l2-economics" / "src",
    REPO_ROOT / "packages" / "l1-chain" / "src",
    REPO_ROOT / "packages" / "wallet-kernel" / "src",
    REPO_ROOT / "packages" / "e2e-demo" / "src",
]
for path in PATHS:
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from e2e_demo.hashing import sha256  # noqa: E402
from nyx_first_app.app import AppError, run_app  # noqa: E402


class AppInvalidArgsTests(unittest.TestCase):
    def test_invalid_seed_rejected(self):
        secret_hex = sha256(b"NYX:W7:ROOT:" + b"123").hex()
        with self.assertRaises(AppError) as ctx:
            run_app(seed="bad", out_path="/tmp/nyx_app_bad.json")  # type: ignore[arg-type]
        self.assertNotIn(secret_hex, str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
