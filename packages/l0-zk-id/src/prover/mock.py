from __future__ import annotations

import hashlib
import hmac

from binding import PROTOCOL_VERSION, BindingError, compute_binding_tag, require_bytes32
from canonical import CanonicalizationError, canonicalize
from envelope import EnvelopeError, ProofEnvelope, create_default_envelope

MOCK_PROOF_DOMAIN = b"NYX:MOCK_PROOF:v1"
MOCK_WITNESS_FIELD = "_mock_witness_hash"


class MockProverError(ValueError):
    pass


def prove_mock(
    *,
    statement_id: str,
    context_id: bytes,
    nonce: bytes,
    public_inputs: dict,
    witness: object,
    nullifier: bytes | None = None,
) -> ProofEnvelope:
    if not isinstance(public_inputs, dict):
        raise MockProverError("public_inputs must be a dict")
    if MOCK_WITNESS_FIELD in public_inputs:
        raise MockProverError("public_inputs must not include _mock_witness_hash")

    witness_hash = _compute_witness_hash(witness)
    prepared_inputs = dict(public_inputs)
    prepared_inputs[MOCK_WITNESS_FIELD] = witness_hash.hex()

    try:
        binding_tag = compute_binding_tag(
            PROTOCOL_VERSION,
            statement_id,
            require_bytes32(context_id, "context_id"),
            require_bytes32(nonce, "nonce"),
            prepared_inputs,
        )
    except BindingError as exc:
        raise MockProverError(str(exc)) from exc

    proof_bytes = _compute_mock_proof(binding_tag, witness_hash)
    try:
        return create_default_envelope(
            statement_id=statement_id,
            context_id=context_id,
            nonce=nonce,
            public_inputs=prepared_inputs,
            proof_bytes=proof_bytes,
            nullifier=nullifier,
        )
    except EnvelopeError as exc:
        raise MockProverError(str(exc)) from exc


def verify_mock_proof(envelope: ProofEnvelope) -> bool:
    try:
        witness_hash = _read_witness_hash(envelope.public_inputs)
    except MockProverError:
        return False
    expected = _compute_mock_proof(envelope.binding_tag, witness_hash)
    if not isinstance(envelope.proof_bytes, bytes):
        return False
    return hmac.compare_digest(expected, envelope.proof_bytes)


def _compute_witness_hash(witness: object) -> bytes:
    try:
        canonical = canonicalize(witness)
    except CanonicalizationError as exc:
        raise MockProverError(str(exc)) from exc
    return hashlib.sha256(canonical).digest()


def _read_witness_hash(public_inputs: dict) -> bytes:
    if not isinstance(public_inputs, dict):
        raise MockProverError("public_inputs must be a dict")
    raw = public_inputs.get(MOCK_WITNESS_FIELD)
    if not isinstance(raw, str):
        raise MockProverError("_mock_witness_hash must be a hex string")
    if len(raw) != 64:
        raise MockProverError("_mock_witness_hash must be 32 bytes")
    try:
        return bytes.fromhex(raw)
    except ValueError as exc:
        raise MockProverError("_mock_witness_hash must be hex") from exc


def _compute_mock_proof(binding_tag: bytes, witness_hash: bytes) -> bytes:
    return hashlib.sha256(MOCK_PROOF_DOMAIN + binding_tag + witness_hash).digest()
