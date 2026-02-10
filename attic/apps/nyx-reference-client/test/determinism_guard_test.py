import json
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


class DeterminismGuardTests(unittest.TestCase):
    def test_same_seed_same_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out1 = f"{tmpdir}/report1.json"
            out2 = f"{tmpdir}/report2.json"
            summary1 = run_client(seed=123, out_path=out1, steps=2)
            summary2 = run_client(seed=123, out_path=out2, steps=2)

            self.assertEqual(summary1.state_hash_hex, summary2.state_hash_hex)
            self.assertEqual(summary1.receipt_chain_hex, summary2.receipt_chain_hex)
            self.assertEqual(summary1.replay_ok, summary2.replay_ok)

            with open(out1, "r", encoding="utf-8") as f1:
                report1 = json.load(f1)
            with open(out2, "r", encoding="utf-8") as f2:
                report2 = json.load(f2)
            self.assertEqual(report1, report2)


if __name__ == "__main__":
    unittest.main()
