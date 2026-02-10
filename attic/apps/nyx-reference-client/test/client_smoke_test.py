import json
import os
import sys
import tempfile
from pathlib import Path
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
PATHS = [
    REPO_ROOT / "apps" / "nyx-reference-client" / "src",
    REPO_ROOT / "packages" / "l3-router" / "src",
    REPO_ROOT / "packages" / "l3-dex" / "src",
]
for path in PATHS:
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from nyx_reference_client.app import run_client  # noqa: E402


class ClientSmokeTests(unittest.TestCase):
    def test_run_and_replay_ok(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "report.json")
            summary = run_client(seed=123, out_path=out_path, steps=2)
            self.assertTrue(summary.replay_ok)
            self.assertEqual(len(summary.state_hash_hex), 64)
            self.assertEqual(len(summary.receipt_chain_hex), 64)
            self.assertTrue(os.path.exists(out_path))
            with open(out_path, "r", encoding="utf-8") as handle:
                report = json.load(handle)
            self.assertIn("pool", report)
            self.assertIn("step_panel", report)
            self.assertEqual(len(report["step_panel"]), 2)


if __name__ == "__main__":
    unittest.main()
