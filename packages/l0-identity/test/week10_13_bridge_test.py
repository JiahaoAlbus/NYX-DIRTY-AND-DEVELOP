import unittest
from pathlib import Path


def load_tests(loader, tests, pattern):
    repo_root = Path(__file__).resolve().parents[3]
    targets = [
        repo_root / "packages" / "conformance-v1" / "test",
        repo_root / "apps" / "nyx-first-app" / "test",
        repo_root / "packages" / "q3-interfaces" / "test",
    ]
    suite = unittest.TestSuite()
    bridge_loader = unittest.TestLoader()
    for target in targets:
        if not target.exists():
            raise RuntimeError(f"test directory missing: {target}")
        if "apps" in target.parts or "q3-interfaces" in target.parts:
            suite.addTests(
                bridge_loader.discover(
                    str(target),
                    pattern="*_test.py",
                    top_level_dir=str(target),
                )
            )
        else:
            suite.addTests(bridge_loader.discover(str(target), pattern="*_test.py"))
    return suite
