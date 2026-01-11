import unittest
from pathlib import Path


def load_tests(loader, tests, pattern):
    repo_root = Path(__file__).resolve().parents[3]
    start_dir = repo_root / "packages" / "conformance-v1" / "test"
    if not start_dir.exists():
        raise RuntimeError("conformance-v1 tests directory is missing")
    bridge_loader = unittest.TestLoader()
    return bridge_loader.discover(str(start_dir), pattern="*_test.py")
