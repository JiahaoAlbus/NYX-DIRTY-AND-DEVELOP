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
from l2_private_ledger.proof_wiring import (  # noqa: E402
    prove_private_action_mock,
    verify_private_action,
)
from l2_private_ledger.state import empty_state, state_root  # noqa: E402
from l2_private_ledger.types import sha256, xor_one_bit  # noqa: E402


class TamperFieldsTests(unittest.TestCase):
    def test_tamper_fields_fail_verification(self):
        state = empty_state()
        commitment = sha256(b"commitment")
        action = LedgerAction(ActionKind.PRIVATE_MINT, PrivateMint(commitment))
        nonce = sha256(b"nonce")
        envelope = prove_private_action_mock(state, action, nonce, witness={"tag": "t"})

        public_inputs = dict(envelope.public_inputs)
        root_bytes = bytes.fromhex(public_inputs["ledger_root"])
        public_inputs["ledger_root"] = xor_one_bit(root_bytes, 3).hex()
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

        public_inputs = dict(envelope.public_inputs)
        hash_bytes = bytes.fromhex(public_inputs["action_hash"])
        public_inputs["action_hash"] = xor_one_bit(hash_bytes, 7).hex()
        tampered_hash = ProofEnvelope(
            protocol_version=envelope.protocol_version,
            statement_id=envelope.statement_id,
            context_id=envelope.context_id,
            nonce=envelope.nonce,
            public_inputs=public_inputs,
            proof_bytes=envelope.proof_bytes,
            binding_tag=envelope.binding_tag,
            nullifier=envelope.nullifier,
        )
        self.assertFalse(verify_private_action(tampered_hash, state_root(state), action))

        bad_nonce = xor_one_bit(envelope.nonce, 1)
        tampered_nonce = ProofEnvelope(
            protocol_version=envelope.protocol_version,
            statement_id=envelope.statement_id,
            context_id=envelope.context_id,
            nonce=bad_nonce,
            public_inputs=envelope.public_inputs,
            proof_bytes=envelope.proof_bytes,
            binding_tag=envelope.binding_tag,
            nullifier=envelope.nullifier,
        )
        self.assertFalse(verify_private_action(tampered_nonce, state_root(state), action))

        bad_tag = xor_one_bit(envelope.binding_tag, 5)
        tampered_tag = ProofEnvelope(
            protocol_version=envelope.protocol_version,
            statement_id=envelope.statement_id,
            context_id=envelope.context_id,
            nonce=envelope.nonce,
            public_inputs=envelope.public_inputs,
            proof_bytes=envelope.proof_bytes,
            binding_tag=bad_tag,
            nullifier=envelope.nullifier,
        )
        self.assertFalse(verify_private_action(tampered_tag, state_root(state), action))

        bad_proof = xor_one_bit(envelope.proof_bytes, 9)
        tampered_proof = ProofEnvelope(
            protocol_version=envelope.protocol_version,
            statement_id=envelope.statement_id,
            context_id=envelope.context_id,
            nonce=envelope.nonce,
            public_inputs=envelope.public_inputs,
            proof_bytes=bad_proof,
            binding_tag=envelope.binding_tag,
            nullifier=envelope.nullifier,
        )
        self.assertFalse(verify_private_action(tampered_proof, state_root(state), action))


if __name__ == "__main__":
    unittest.main()
