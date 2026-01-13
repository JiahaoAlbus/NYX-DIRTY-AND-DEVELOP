import sys
from pathlib import Path
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = REPO_ROOT / "packages" / "l2-private-ledger" / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from l2_private_ledger.errors import ValidationError  # noqa: E402
from l2_private_ledger.types import ensure_bytes32, xor_one_bit  # noqa: E402


class Bytes32Tests(unittest.TestCase):
    def test_bytes32_validation(self):
        good = b"\x00" * 32
        self.assertEqual(ensure_bytes32(good, "good"), good)
        with self.assertRaises(ValidationError):
            ensure_bytes32("bad", "bad")  # type: ignore[arg-type]
        with self.assertRaises(ValidationError):
            ensure_bytes32(b"\x00" * 31, "bad")

    def test_xor_one_bit(self):
        base = b"\x00" * 32
        mutated = xor_one_bit(base, 0)
        self.assertEqual(len(mutated), 32)
        self.assertNotEqual(base, mutated)


if __name__ == "__main__":
    unittest.main()
