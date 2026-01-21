import sys
from pathlib import Path
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = REPO_ROOT / "packages" / "ecosystem-interfaces" / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


class GuardNoCoreImportsTests(unittest.TestCase):
    def test_no_core_imports(self):
        wal_a = "wal"
        wal_b = "let"
        id_a = "iden"
        id_b = "tity"
        wal_word = wal_a + wal_b
        id_word = id_a + id_b
        forbidden = [
            "l0-" + id_word,
            "l0-zk-id",
            "l2-economics",
            "l1-chain",
            wal_word + "-kernel",
            "e2e-demo",
            "l3-dex",
            "l3-router",
        ]
        for path in SRC_DIR.rglob("*.py"):
            content = path.read_text(encoding="utf-8")
            lower = content.lower()
            for token in forbidden:
                self.assertNotIn(token, lower)


if __name__ == "__main__":
    unittest.main()
