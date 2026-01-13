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

from e2e_demo.replay import replay_and_verify  # noqa: E402
from e2e_demo.trace import E2ETrace  # noqa: E402
from nyx_first_app.app import run_app  # noqa: E402


class AppSmokeTests(unittest.TestCase):
    def test_app_smoke(self):
        fd, out_path = tempfile.mkstemp(prefix="nyx_app_", suffix=".json")
        os.close(fd)
        try:
            summary = run_app(seed=123, out_path=out_path)
            self.assertTrue(summary.replay_ok)
            raw = Path(out_path).read_text(encoding="utf-8")
            trace = E2ETrace.from_json(raw)
            replay = replay_and_verify(trace)
            self.assertTrue(replay.ok)
        finally:
            try:
                os.unlink(out_path)
            except OSError:
                pass


if __name__ == "__main__":
    unittest.main()
