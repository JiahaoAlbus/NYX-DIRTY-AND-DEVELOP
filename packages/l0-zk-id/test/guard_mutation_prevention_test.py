import hashlib
import os
import sys
import unittest

SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from binding import PROTOCOL_VERSION, compute_binding_tag  # noqa: E402
from canonical import CanonicalizationError, canonicalize  # noqa: E402
from nullifier import compute_nullifier  # noqa: E402


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

    def test_bool_and_int_distinct(self):
        self.assertNotEqual(canonicalize(True), canonicalize(1))
        self.assertNotEqual(canonicalize(False), canonicalize(0))

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


if __name__ == "__main__":
    unittest.main()
