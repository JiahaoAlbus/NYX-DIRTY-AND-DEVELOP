import hashlib
import os
import sys
import unittest

SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from envelope import ProofEnvelope  # noqa: E402
from prover.mock import prove_mock  # noqa: E402
from verifier import MockProofAdapter, verify  # noqa: E402


def _bytes32(label: str) -> bytes:
    return hashlib.sha256(label.encode("ascii")).digest()


class ContextSeparationUnitTests(unittest.TestCase):
    def setUp(self):
        self.adapter = MockProofAdapter()
        self.statement_id = "personhood.v0"
        self.context_id = _bytes32("context-1")
        self.nonce = _bytes32("nonce-1")
        self.public_inputs = {"claim": True, "level": 2}
        self.witness = {"secret": "value"}

    def _prove(self) -> ProofEnvelope:
        return prove_mock(
            statement_id=self.statement_id,
            context_id=self.context_id,
            nonce=self.nonce,
            public_inputs=self.public_inputs,
            witness=self.witness,
        )

    def test_prove_and_verify_same_context(self):
        envelope = self._prove()
        self.assertTrue(verify(envelope, self.context_id, self.statement_id, self.adapter))

    def test_verify_fails_for_wrong_context(self):
        envelope = self._prove()
        other_context = _bytes32("context-2")
        self.assertFalse(verify(envelope, other_context, self.statement_id, self.adapter))

    def test_tamper_context_id_binding_tag_mismatch(self):
        envelope = self._prove()
        tampered_context = _bytes32("context-3")
        tampered = ProofEnvelope(
            protocol_version=envelope.protocol_version,
            statement_id=envelope.statement_id,
            context_id=tampered_context,
            nonce=envelope.nonce,
            public_inputs=envelope.public_inputs,
            proof_bytes=envelope.proof_bytes,
            binding_tag=envelope.binding_tag,
            nullifier=envelope.nullifier,
        )
        self.assertFalse(verify(tampered, tampered_context, self.statement_id, self.adapter))

    def test_tamper_binding_tag(self):
        envelope = self._prove()
        tampered = ProofEnvelope(
            protocol_version=envelope.protocol_version,
            statement_id=envelope.statement_id,
            context_id=envelope.context_id,
            nonce=envelope.nonce,
            public_inputs=envelope.public_inputs,
            proof_bytes=envelope.proof_bytes,
            binding_tag=_bytes32("binding-tag"),
            nullifier=envelope.nullifier,
        )
        self.assertFalse(verify(tampered, self.context_id, self.statement_id, self.adapter))

    def test_modify_public_inputs(self):
        envelope = self._prove()
        changed_inputs = dict(envelope.public_inputs)
        changed_inputs["level"] = 3
        tampered = ProofEnvelope(
            protocol_version=envelope.protocol_version,
            statement_id=envelope.statement_id,
            context_id=envelope.context_id,
            nonce=envelope.nonce,
            public_inputs=changed_inputs,
            proof_bytes=envelope.proof_bytes,
            binding_tag=envelope.binding_tag,
            nullifier=envelope.nullifier,
        )
        self.assertFalse(verify(tampered, self.context_id, self.statement_id, self.adapter))

    def test_statement_id_mismatch(self):
        envelope = self._prove()
        self.assertFalse(verify(envelope, self.context_id, "rep.threshold.v0", self.adapter))

    def test_protocol_version_mismatch(self):
        envelope = self._prove()
        tampered = ProofEnvelope(
            protocol_version="NYX-ZKID/0.0",
            statement_id=envelope.statement_id,
            context_id=envelope.context_id,
            nonce=envelope.nonce,
            public_inputs=envelope.public_inputs,
            proof_bytes=envelope.proof_bytes,
            binding_tag=envelope.binding_tag,
            nullifier=envelope.nullifier,
        )
        self.assertFalse(verify(tampered, self.context_id, self.statement_id, self.adapter))


if __name__ == "__main__":
    unittest.main()
