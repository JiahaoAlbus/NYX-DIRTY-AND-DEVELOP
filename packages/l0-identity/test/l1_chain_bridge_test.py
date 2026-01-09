import unittest
from pathlib import Path


def load_tests(loader, tests, pattern):
    repo_root = Path(__file__).resolve().parents[3]
    start_dir = repo_root / "packages" / "l1-chain" / "test"
    if not start_dir.exists():
        raise RuntimeError("l1-chain tests directory is missing")
    bridge_loader = unittest.TestLoader()
    return bridge_loader.discover(str(start_dir), pattern="*_test.py")
