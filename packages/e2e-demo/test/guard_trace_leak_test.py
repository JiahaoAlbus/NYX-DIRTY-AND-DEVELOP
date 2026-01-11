import contextlib
import io
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PATHS = [
    REPO_ROOT / "packages" / "e2e-demo" / "src",
    REPO_ROOT / "packages" / "l0-zk-id" / "src",
    REPO_ROOT / "packages" / "l2-economics" / "src",
    REPO_ROOT / "packages" / "l1-chain" / "src",
    REPO_ROOT / "packages" / "wallet-kernel" / "src",
]
for path in PATHS:
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from e2e_demo.hashing import sha256  # noqa: E402
from e2e_demo.pipeline import run_e2e  # noqa: E402


class TraceLeakGuardTests(unittest.TestCase):
    def test_root_secret_not_leaked(self):
        seed = 123
        root_secret = sha256(b"NYX:W7:ROOT:" + str(seed).encode("ascii"))
        secret_hex = root_secret.hex()

        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            trace, summary = run_e2e(seed=seed)
        trace_json = trace.to_json()
        combined = buffer.getvalue() + trace_json + repr(trace) + repr(summary)
        self.assertNotIn(secret_hex, combined)


if __name__ == "__main__":
    unittest.main()
