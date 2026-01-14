import io
import sys
from contextlib import redirect_stdout
from pathlib import Path
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = REPO_ROOT / "packages" / "e2e-private-transfer" / "src"
PL_SRC = REPO_ROOT / "packages" / "l2-private-ledger" / "src"
ZK_SRC = REPO_ROOT / "packages" / "l0-zk-id" / "src"
ECON_SRC = REPO_ROOT / "packages" / "l2-economics" / "src"
CHAIN_SRC = REPO_ROOT / "packages" / "l1-chain" / "src"
KERNEL_SRC = REPO_ROOT / "packages" / "wallet-kernel" / "src"
for path in (SRC_DIR, PL_SRC, ZK_SRC, ECON_SRC, CHAIN_SRC, KERNEL_SRC):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from e2e_private_transfer.pipeline import _derive_root_secret, run_private_transfer  # noqa: E402


class SecretLeakGuardTests(unittest.TestCase):
    def test_no_secret_in_outputs(self):
        seed = 123
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            trace, summary = run_private_transfer(seed=seed)
        root_secret = _derive_root_secret(seed)
        secret_hex = root_secret.hex()
        combined = "".join(
            [
                buffer.getvalue(),
                trace.to_json(),
                repr(trace),
                repr(summary),
            ]
        )
        self.assertNotIn(secret_hex, combined)


if __name__ == "__main__":
    unittest.main()
