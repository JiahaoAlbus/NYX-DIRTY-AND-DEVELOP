import sys
from pathlib import Path
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = REPO_ROOT / "packages" / "ecosystem-interfaces" / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ecosystem_interfaces import (  # noqa: E402
    ChatModule,
    EntertainmentModule,
    MarketplaceModule,
    ModuleContext,
    ModuleId,
    RequestId,
)


class SkeletonImportTests(unittest.TestCase):
    def test_imports(self):
        self.assertTrue(MarketplaceModule)
        self.assertTrue(ChatModule)
        self.assertTrue(EntertainmentModule)
        self.assertTrue(ModuleId("mod"))
        self.assertTrue(RequestId("req"))
        self.assertTrue(ModuleContext(ModuleId("mod")))


if __name__ == "__main__":
    unittest.main()
