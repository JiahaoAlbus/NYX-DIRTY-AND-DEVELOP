import sys
from pathlib import Path
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
PL_SRC = REPO_ROOT / "packages" / "l2-private-ledger" / "src"
ZK_SRC = REPO_ROOT / "packages" / "l0-zk-id" / "src"
for path in (PL_SRC, ZK_SRC):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from l2_private_ledger.actions import ActionKind, LedgerAction, PrivateMint  # noqa: E402
from l2_private_ledger.errors import ValidationError  # noqa: E402
from l2_private_ledger.proof_wiring import (  # noqa: E402
    build_public_inputs,
    compute_action_hash,
    validate_public_inputs_shape,
)
from l2_private_ledger.state import empty_state, state_root  # noqa: E402
from l2_private_ledger.types import sha256  # noqa: E402


class StatementValidationTests(unittest.TestCase):
    def setUp(self):
        self.state = empty_state()
        self.action = LedgerAction(
            ActionKind.PRIVATE_MINT,
            PrivateMint(sha256(b"commitment")),
        )
        self.root = state_root(self.state)
        self.action_hash = compute_action_hash(self.action)
        self.inputs = build_public_inputs(self.root, self.action, self.action_hash)

    def test_missing_required_fields(self):
        for key in ("ledger_root", "action_hash", "action_kind", "payload", "v"):
            inputs = dict(self.inputs)
            inputs.pop(key)
            with self.assertRaises(ValidationError):
                validate_public_inputs_shape(inputs)

    def test_rejects_bytes_and_float(self):
        inputs = dict(self.inputs)
        inputs["payload"] = {"commitment": b"\x00" * 32}
        with self.assertRaises(ValidationError):
            validate_public_inputs_shape(inputs)

        inputs = dict(self.inputs)
        inputs["v"] = 1.25
        with self.assertRaises(ValidationError):
            validate_public_inputs_shape(inputs)


if __name__ == "__main__":
    unittest.main()
