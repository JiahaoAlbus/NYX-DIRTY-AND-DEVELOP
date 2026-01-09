import hashlib
import hmac
import os
import sys
import unittest

SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from binding import PROTOCOL_VERSION, build_binding_preimage, compute_binding_tag  # noqa: E402
from canonical import (  # noqa: E402
    MAX_CANONICAL_BYTES,
    MAX_CANONICAL_DEPTH,
    CanonicalizationError,
    canonicalize,
)
from nullifier import compute_nullifier  # noqa: E402
from prover.mock import prove_mock, verify_mock_proof  # noqa: E402
from verifier import verify_envelope  # noqa: E402


def _bytes32(label: str) -> bytes:
    return hashlib.sha256(label.encode("ascii")).digest()


def _binding_tag(statement_id: str, context_id: bytes, nonce: bytes, public_inputs: dict) -> bytes:
    return compute_binding_tag(
        PROTOCOL_VERSION,
        statement_id,
        context_id,
        nonce,
        public_inputs,
    )


class GuardMutationPreventionTests(unittest.TestCase):
    def test_binding_tag_depends_on_context_id(self):
        base = _binding_tag("personhood.v0", _bytes32("c1"), _bytes32("n1"), {"a": 1})
        other = _binding_tag("personhood.v0", _bytes32("c2"), _bytes32("n1"), {"a": 1})
        self.assertNotEqual(base, other)

    def test_binding_tag_depends_on_nonce(self):
        base = _binding_tag("personhood.v0", _bytes32("c1"), _bytes32("n1"), {"a": 1})
        other = _binding_tag("personhood.v0", _bytes32("c1"), _bytes32("n2"), {"a": 1})
        self.assertNotEqual(base, other)

    def test_binding_tag_depends_on_statement_id(self):
        base = _binding_tag("personhood.v0", _bytes32("c1"), _bytes32("n1"), {"a": 1})
        other = _binding_tag("rep.threshold.v0", _bytes32("c1"), _bytes32("n1"), {"a": 1})
        self.assertNotEqual(base, other)

    def test_binding_tag_depends_on_public_inputs(self):
        base = _binding_tag("personhood.v0", _bytes32("c1"), _bytes32("n1"), {"a": 1})
        other = _binding_tag("personhood.v0", _bytes32("c1"), _bytes32("n1"), {"a": 2})
        self.assertNotEqual(base, other)

    def test_binding_preimage_resists_ambiguity(self):
        inputs = {"a": 1}
        context_id = _bytes32("context")
        nonce = _bytes32("nonce")
        first = build_binding_preimage(
            protocol_version="ab",
            statement_id="c",
            context_id=context_id,
            nonce=nonce,
            public_inputs=inputs,
        )
        second = build_binding_preimage(
            protocol_version="a",
            statement_id="bc",
            context_id=context_id,
            nonce=nonce,
            public_inputs=inputs,
        )
        self.assertNotEqual(first, second)

    def test_canonicalization_key_order_equivalent(self):
        first = {"a": 1, "b": [2, 3], "c": {"x": True, "y": None}}
        second = {"c": {"y": None, "x": True}, "b": [2, 3], "a": 1}
        self.assertEqual(canonicalize(first), canonicalize(second))

    def test_canonicalization_rejects_illegal_types(self):
        with self.assertRaises(CanonicalizationError):
            canonicalize(1.5)
        with self.assertRaises(CanonicalizationError):
            canonicalize(float("nan"))
        with self.assertRaises(CanonicalizationError):
            canonicalize(b"bytes")
        with self.assertRaises(CanonicalizationError):
            canonicalize(bytearray(b"bytes"))
        with self.assertRaises(CanonicalizationError):
            canonicalize(set([1, 2]))
        with self.assertRaises(CanonicalizationError):
            canonicalize("\ud800")
        with self.assertRaises(CanonicalizationError):
            canonicalize({"bad": "\ud800"})

    def test_bool_and_int_distinct(self):
        self.assertNotEqual(canonicalize(True), canonicalize(1))
        self.assertNotEqual(canonicalize(False), canonicalize(0))

    def test_canonicalization_max_depth_guard(self):
        value = "leaf"
        for _ in range(MAX_CANONICAL_DEPTH + 1):
            value = [value]
        with self.assertRaises(CanonicalizationError):
            canonicalize(value)

    def test_canonicalization_max_bytes_guard(self):
        payload = {"data": "a" * (MAX_CANONICAL_BYTES + 1)}
        with self.assertRaises(CanonicalizationError):
            canonicalize(payload)

    def test_nullifier_depends_on_context_id(self):
        base = compute_nullifier(
            context_id=_bytes32("c1"),
            statement_id="personhood.v0",
            epoch_or_nonce=_bytes32("epoch"),
            secret_commitment=_bytes32("secret"),
        )
        other = compute_nullifier(
            context_id=_bytes32("c2"),
            statement_id="personhood.v0",
            epoch_or_nonce=_bytes32("epoch"),
            secret_commitment=_bytes32("secret"),
        )
        self.assertNotEqual(base, other)

    def test_verify_envelope_uses_compare_digest(self):
        nullifier = compute_nullifier(
            context_id=_bytes32("ctx"),
            statement_id="personhood.v0",
            epoch_or_nonce=_bytes32("epoch"),
            secret_commitment=_bytes32("secret"),
        )
        envelope = prove_mock(
            statement_id="personhood.v0",
            context_id=_bytes32("ctx"),
            nonce=_bytes32("nonce"),
            public_inputs={"a": 1},
            witness={"secret": "value"},
            nullifier=nullifier,
        )
        calls = {"count": 0, "args": []}
        original = hmac.compare_digest

        def wrapped(a, b):
            calls["count"] += 1
            calls["args"].append((bytes(a), bytes(b)))
            return original(a, b)

        hmac.compare_digest = wrapped
        try:
            self.assertTrue(
                verify_envelope(
                    envelope,
                    envelope.context_id,
                    envelope.statement_id,
                    expected_nullifier=nullifier,
                )
            )
        finally:
            hmac.compare_digest = original
        self.assertGreater(calls["count"], 0)
        self.assertTrue(
            any(
                (pair[0] == nullifier and pair[1] == nullifier)
                or (pair[0] == nullifier and pair[1] == envelope.nullifier)
                or (pair[1] == nullifier and pair[0] == envelope.nullifier)
                for pair in calls["args"]
            )
        )

    def test_verify_mock_proof_uses_compare_digest(self):
        envelope = prove_mock(
            statement_id="personhood.v0",
            context_id=_bytes32("ctx"),
            nonce=_bytes32("nonce"),
            public_inputs={"a": 1},
            witness={"secret": "value"},
        )
        calls = {"count": 0}
        original = hmac.compare_digest

        def wrapped(a, b):
            calls["count"] += 1
            return original(a, b)

        hmac.compare_digest = wrapped
        try:
            self.assertTrue(verify_mock_proof(envelope))
        finally:
            hmac.compare_digest = original
        self.assertGreater(calls["count"], 0)


if __name__ == "__main__":
    unittest.main()
