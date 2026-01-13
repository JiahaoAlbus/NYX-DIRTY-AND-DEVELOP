import inspect
import sys
from pathlib import Path
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = REPO_ROOT / "packages" / "l0-reputation" / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from l0_reputation.interfaces import DisclosureStatement, ReputationKernel  # noqa: E402


class GuardContextBindingTests(unittest.TestCase):
    def test_interfaces_require_context_id(self):
        kernel_sig = inspect.signature(ReputationKernel.record_event)
        self.assertIn("context_id", kernel_sig.parameters)
        verify_sig = inspect.signature(ReputationKernel.verify_disclosure)
        self.assertIn("context_id", verify_sig.parameters)
        self.assertTrue(hasattr(DisclosureStatement, "context_id"))


if __name__ == "__main__":
    unittest.main()
