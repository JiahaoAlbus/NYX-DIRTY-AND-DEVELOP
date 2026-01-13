import os
from pathlib import Path
import unittest


class Q3InterfacesNoRuntimeDependencyTests(unittest.TestCase):
    def test_no_runtime_imports(self):
        repo_root = Path(__file__).resolve().parents[3]
        targets = [
            repo_root / "packages" / "e2e-demo" / "src",
            repo_root / "apps" / "nyx-first-app" / "src",
            repo_root / "packages" / "conformance-v1" / "src",
        ]
        for target in targets:
            for root, _, files in os.walk(target):
                for file_name in files:
                    if not file_name.endswith(".py"):
                        continue
                    path = Path(root) / file_name
                    content = path.read_text(encoding="utf-8")
                    self.assertNotIn("q3_interfaces", content, msg=str(path))


if __name__ == "__main__":
    unittest.main()
