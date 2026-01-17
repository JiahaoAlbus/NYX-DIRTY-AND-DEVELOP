import sys
from pathlib import Path
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_DIRS = [
    REPO_ROOT / "packages" / "l3-router" / "src",
    REPO_ROOT / "packages" / "l3-dex" / "src",
]
for path in SRC_DIRS:
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

import l3_router  # noqa: E402


class SkeletonImportTests(unittest.TestCase):
    def test_imports(self) -> None:
        self.assertTrue(hasattr(l3_router, "RouterActionKind"))
        self.assertTrue(hasattr(l3_router, "RouteSwap"))
        self.assertTrue(hasattr(l3_router, "RouterAction"))
        self.assertTrue(hasattr(l3_router, "RouterState"))
        self.assertTrue(hasattr(l3_router, "RouterReceipt"))
        self.assertTrue(hasattr(l3_router, "apply_route"))
        self.assertTrue(hasattr(l3_router, "replay_route"))
        self.assertTrue(hasattr(l3_router, "state_hash"))
        self.assertTrue(hasattr(l3_router, "route_state_hash"))


if __name__ == "__main__":
    unittest.main()
