import json
import os
import sys
import tempfile
from pathlib import Path
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = REPO_ROOT / "packages" / "conformance-v1" / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from conformance_v1.runner import main  # noqa: E402


class RunnerOutfileTests(unittest.TestCase):
    def test_runner_writes_report(self):
        fd, path = tempfile.mkstemp(prefix="nyx_conf_", suffix=".json", dir="/tmp")
        os.close(fd)
        try:
            exit_code = main(["--out", path])
            self.assertEqual(exit_code, 0)
            raw = Path(path).read_text(encoding="utf-8")
            payload = json.loads(raw)
            self.assertIn("rules", payload)
            self.assertIn("results", payload)
            self.assertIn("attack_cards", payload)
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass


if __name__ == "__main__":
    unittest.main()
