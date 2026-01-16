import unittest

import l3_router


class SkeletonImportTests(unittest.TestCase):
    def test_imports(self) -> None:
        self.assertTrue(hasattr(l3_router, "RouterActionKind"))
        self.assertTrue(hasattr(l3_router, "RouteSwap"))
        self.assertTrue(hasattr(l3_router, "RouterAction"))
        self.assertTrue(hasattr(l3_router, "RouterState"))
        self.assertTrue(hasattr(l3_router, "RouterReceipt"))
        self.assertTrue(hasattr(l3_router, "replay_route"))
        self.assertTrue(hasattr(l3_router, "check_invariants"))


if __name__ == "__main__":
    unittest.main()
