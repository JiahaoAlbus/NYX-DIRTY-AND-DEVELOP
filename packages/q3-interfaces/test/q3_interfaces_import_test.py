import sys
from pathlib import Path
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = REPO_ROOT / "packages" / "q3-interfaces" / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


class Q3InterfacesImportTests(unittest.TestCase):
    def test_imports(self):
        import q3_interfaces

        self.assertTrue(hasattr(q3_interfaces, "ProofProvider"))
        self.assertTrue(hasattr(q3_interfaces, "ProofVerifier"))
        self.assertTrue(hasattr(q3_interfaces, "FeePolicyHook"))
        self.assertTrue(hasattr(q3_interfaces, "ChainFinalityProvider"))
        self.assertTrue(hasattr(q3_interfaces, "ReceiptVerifier"))
        self.assertTrue(hasattr(q3_interfaces, "Bytes32"))


if __name__ == "__main__":
    unittest.main()
