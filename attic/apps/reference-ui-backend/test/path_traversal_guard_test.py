import tempfile
import unittest
from pathlib import Path

from nyx_reference_ui_backend import evidence


class PathTraversalGuardTest(unittest.TestCase):
    def test_invalid_run_id_rejected(self):
        cases = [
            "../",
            "..\\",
            "/etc",
            "a/../../b",
            "a%2f..",
            "a..",
            "a b",
            "",
        ]
        for value in cases:
            with self.subTest(run_id=value):
                with self.assertRaises(evidence.EvidenceError):
                    evidence._sanitize_run_id(value)

    def test_invalid_artifact_name_rejected(self):
        cases = [
            "../x",
            "subdir/file",
            "/abs",
            "..\\x",
            "",
        ]
        for value in cases:
            with self.subTest(name=value):
                with self.assertRaises(evidence.EvidenceError):
                    evidence._validate_artifact_name(value)

    def test_safe_artifact_path_with_valid_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_root = Path(tmp)
            run_id = "seed-123"
            artifact = "stdout.txt"
            path = evidence._safe_artifact_path(run_root, run_id, artifact)
            self.assertTrue(path.name == artifact)
            self.assertTrue(run_root.resolve() in path.resolve().parents)


if __name__ == "__main__":
    unittest.main()
