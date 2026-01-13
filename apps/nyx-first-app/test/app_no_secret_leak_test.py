import contextlib
import io
import os
import sys
import tempfile
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
from e2e_demo.trace import E2ETrace  # noqa: E402
from nyx_first_app import cli  # noqa: E402


class AppNoSecretLeakTests(unittest.TestCase):
    def test_no_secret_in_outputs(self):
        seed = 123
        secret_hex = sha256(b"NYX:W7:ROOT:" + str(seed).encode("ascii")).hex()

        fd, out_path = tempfile.mkstemp(prefix="nyx_app_", suffix=".json")
        os.close(fd)
        buffer = io.StringIO()
        argv = ["nyx_first_app.cli", "--seed", str(seed), "--out", out_path]
        try:
            with contextlib.redirect_stdout(buffer):
                with contextlib.redirect_stderr(buffer):
                    original_argv = sys.argv
                    sys.argv = argv
                    try:
                        cli.main()
                    finally:
                        sys.argv = original_argv
            raw = Path(out_path).read_text(encoding="utf-8")
            trace = E2ETrace.from_json(raw)
            combined = buffer.getvalue() + raw + repr(trace)
            self.assertNotIn(secret_hex, combined)
        finally:
            try:
                os.unlink(out_path)
            except OSError:
                pass


if __name__ == "__main__":
    unittest.main()
