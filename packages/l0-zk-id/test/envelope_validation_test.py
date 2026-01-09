import hashlib
import os
import sys
import unittest

SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from binding import PROTOCOL_VERSION  # noqa: E402
from envelope import EnvelopeError, ProofEnvelope, create_envelope  # noqa: E402


def _bytes32(label: str) -> bytes:
    return hashlib.sha256(label.encode("ascii")).digest()


class EnvelopeValidationTests(unittest.TestCase):
    def setUp(self):
        self.protocol_version = PROTOCOL_VERSION
        self.statement_id = "personhood.v0"
        self.context_id = _bytes32("context")
        self.nonce = _bytes32("nonce")
        self.public_inputs = {"a": 1}
        self.proof_bytes = _bytes32("proof")
        self.binding_tag = _bytes32("binding")

    def test_create_envelope_rejects_non_bytes_context(self):
        with self.assertRaises(EnvelopeError):
            create_envelope(
                protocol_version=self.protocol_version,
                statement_id=self.statement_id,
                context_id="not-bytes",
                nonce=self.nonce,
                public_inputs=self.public_inputs,
                proof_bytes=self.proof_bytes,
            )

    def test_create_envelope_rejects_nonce_length(self):
        with self.assertRaises(EnvelopeError):
            create_envelope(
                protocol_version=self.protocol_version,
                statement_id=self.statement_id,
                context_id=self.context_id,
                nonce=b"short",
                public_inputs=self.public_inputs,
                proof_bytes=self.proof_bytes,
            )

    def test_create_envelope_rejects_empty_protocol(self):
        with self.assertRaises(EnvelopeError):
            create_envelope(
                protocol_version="",
                statement_id=self.statement_id,
                context_id=self.context_id,
                nonce=self.nonce,
                public_inputs=self.public_inputs,
                proof_bytes=self.proof_bytes,
            )

    def test_create_envelope_rejects_non_string_statement(self):
        with self.assertRaises(EnvelopeError):
            create_envelope(
                protocol_version=self.protocol_version,
                statement_id=123,
                context_id=self.context_id,
                nonce=self.nonce,
                public_inputs=self.public_inputs,
                proof_bytes=self.proof_bytes,
            )

    def test_create_envelope_rejects_invalid_public_inputs(self):
        with self.assertRaises(EnvelopeError):
            create_envelope(
                protocol_version=self.protocol_version,
                statement_id=self.statement_id,
                context_id=self.context_id,
                nonce=self.nonce,
                public_inputs={"bad": b"bytes"},
                proof_bytes=self.proof_bytes,
            )

    def test_envelope_rejects_invalid_binding_tag(self):
        with self.assertRaises(EnvelopeError):
            ProofEnvelope(
                protocol_version=self.protocol_version,
                statement_id=self.statement_id,
                context_id=self.context_id,
                nonce=self.nonce,
                public_inputs=self.public_inputs,
                proof_bytes=self.proof_bytes,
                binding_tag=b"short",
            )

    def test_envelope_rejects_non_bytes_proof(self):
        with self.assertRaises(EnvelopeError):
            ProofEnvelope(
                protocol_version=self.protocol_version,
                statement_id=self.statement_id,
                context_id=self.context_id,
                nonce=self.nonce,
                public_inputs=self.public_inputs,
                proof_bytes=bytearray(b"proof"),
                binding_tag=self.binding_tag,
            )

    def test_envelope_rejects_nullifier_length(self):
        with self.assertRaises(EnvelopeError):
            ProofEnvelope(
                protocol_version=self.protocol_version,
                statement_id=self.statement_id,
                context_id=self.context_id,
                nonce=self.nonce,
                public_inputs=self.public_inputs,
                proof_bytes=self.proof_bytes,
                binding_tag=self.binding_tag,
                nullifier=b"short",
            )


if __name__ == "__main__":
    unittest.main()
