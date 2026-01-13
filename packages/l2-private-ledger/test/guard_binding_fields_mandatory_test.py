import sys
from pathlib import Path
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
PL_SRC = REPO_ROOT / "packages" / "l2-private-ledger" / "src"
ZK_SRC = REPO_ROOT / "packages" / "l0-zk-id" / "src"
for path in (PL_SRC, ZK_SRC):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from envelope import ProofEnvelope  # noqa: E402
from l2_private_ledger.actions import ActionKind, LedgerAction, PrivateMint  # noqa: E402
from l2_private_ledger.errors import ValidationError  # noqa: E402
from l2_private_ledger.proof_wiring import (  # noqa: E402
    build_public_inputs,
    compute_action_hash,
    prove_private_action_mock,
    validate_public_inputs_shape,
    verify_private_action,
)
from l2_private_ledger.state import empty_state, state_root  # noqa: E402
from l2_private_ledger.types import sha256  # noqa: E402


class BindingFieldsGuardTests(unittest.TestCase):
    def test_missing_fields_rejected(self):
        state = empty_state()
        action = LedgerAction(
            ActionKind.PRIVATE_MINT,
            PrivateMint(sha256(b"commitment")),
        )
        root = state_root(state)
        action_hash = compute_action_hash(action)
        public_inputs = build_public_inputs(root, action, action_hash)
        for key in ("ledger_root", "action_hash", "action_kind", "payload", "v"):
            inputs = dict(public_inputs)
            inputs.pop(key)
            with self.assertRaises(ValidationError):
                validate_public_inputs_shape(inputs)

    def test_verify_fails_without_ledger_root(self):
        state = empty_state()
        action = LedgerAction(
            ActionKind.PRIVATE_MINT,
            PrivateMint(sha256(b"commitment-2")),
        )
        nonce = sha256(b"nonce")
        envelope = prove_private_action_mock(state, action, nonce, witness={"t": 1})
        public_inputs = dict(envelope.public_inputs)
        public_inputs.pop("ledger_root")
        tampered = ProofEnvelope(
            protocol_version=envelope.protocol_version,
            statement_id=envelope.statement_id,
            context_id=envelope.context_id,
            nonce=envelope.nonce,
            public_inputs=public_inputs,
            proof_bytes=envelope.proof_bytes,
            binding_tag=envelope.binding_tag,
            nullifier=envelope.nullifier,
        )
        self.assertFalse(verify_private_action(tampered, state_root(state), action))


if __name__ == "__main__":
    unittest.main()
