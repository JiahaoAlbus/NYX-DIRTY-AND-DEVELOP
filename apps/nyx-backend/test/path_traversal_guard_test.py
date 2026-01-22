import tempfile
import unittest
from pathlib import Path
import sys


BACKEND_ROOT = Path(__file__).resolve().parents[1]
SRC = BACKEND_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from nyx_backend import evidence as ev  # noqa: E402


class PathTraversalGuardTests(unittest.TestCase):
    def test_invalid_run_id_rejected(self) -> None:
        for run_id in ["../x", "..", "a/../b", "a b", ""]:
            with self.assertRaises(ev.EvidenceError):
                ev._sanitize_run_id(run_id)

    def test_invalid_artifact_name_rejected(self) -> None:
        for name in ["../x", "subdir/file", "/abs", "..\\x", ""]:
            with self.assertRaises(ev.EvidenceError):
                ev._validate_artifact_name(name)

    def test_safe_artifact_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_id = "safe-run"
            path = ev._safe_artifact_path(root, run_id, "inputs.json")
            self.assertTrue(root.resolve() in path.parents)


if __name__ == "__main__":
    unittest.main()
