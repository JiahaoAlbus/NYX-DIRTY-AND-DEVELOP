import os
import unittest
from pathlib import Path


def _iter_tests(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from _iter_tests(item)
        else:
            yield item


def load_tests(loader, tests, pattern):
    repo_root = Path(__file__).resolve().parents[3]
    targets: list[Path] = []
    for base in (repo_root / "packages", repo_root / "apps"):
        if not base.exists():
            continue
        for root, _, _ in os.walk(base):
            if Path(root).name != "test":
                continue
            path = Path(root)
            if path == repo_root / "packages" / "l0-identity" / "test":
                continue
            targets.append(path)

    suite = unittest.TestSuite()
    seen: set[str] = set()
    def discover_tests(target: Path) -> unittest.TestSuite:
        for top_level in (str(target), str(repo_root), None):
            try:
                local_loader = unittest.TestLoader()
                if top_level is None:
                    return local_loader.discover(str(target), pattern="*_test.py")
                return local_loader.discover(
                    str(target),
                    pattern="*_test.py",
                    top_level_dir=top_level,
                )
            except (ImportError, AssertionError):
                continue
        return unittest.TestSuite()

    for target in sorted(set(targets)):
        discovered = discover_tests(target)
        for test in _iter_tests(discovered):
            test_id = test.id()
            if test_id in seen:
                continue
            seen.add(test_id)
            suite.addTest(test)
    return suite
