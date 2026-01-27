import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest


class SmokeOutDirTests(unittest.TestCase):
    def test_out_dir_dry_run_creates_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "smoke"
            cmd = [
                sys.executable,
                str(Path(__file__).resolve().parents[3] / "scripts" / "nyx_smoke_all_modules.py"),
                "--seed",
                "123",
                "--run-id",
                "dryrun-123",
                "--out-dir",
                str(out_dir),
                "--dry-run",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0)
            manifest_path = out_dir / "manifest.json"
            self.assertTrue(manifest_path.exists())
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(payload.get("seed"), 123)
            self.assertEqual(payload.get("run_id"), "dryrun-123")
            self.assertEqual(payload.get("runs"), [])


if __name__ == "__main__":
    unittest.main()
