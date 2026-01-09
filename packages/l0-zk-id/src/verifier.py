from __future__ import annotations

import hmac

from binding import BindingError, PROTOCOL_VERSION, compute_binding_tag, require_bytes32
from envelope import ProofEnvelope
from prover.mock import verify_mock_proof


class ProofAdapter:
    def verify(self, envelope: ProofEnvelope) -> bool:
        raise NotImplementedError


class MockProofAdapter(ProofAdapter):
    def verify(self, envelope: ProofEnvelope) -> bool:
        return verify_mock_proof(envelope)


def verify_envelope(
    envelope: ProofEnvelope,
    expected_context_id: bytes,
    expected_statement_id: str,
    expected_protocol_version: str = PROTOCOL_VERSION,
) -> bool:
    try:
        expected_context = require_bytes32(expected_context_id, "expected_context_id")
    except BindingError:
        return False
    if not isinstance(envelope, ProofEnvelope):
        return False
    if envelope.protocol_version != expected_protocol_version:
        return False
    if envelope.statement_id != expected_statement_id:
        return False
    try:
        context_bytes = require_bytes32(envelope.context_id, "context_id")
        nonce_bytes = require_bytes32(envelope.nonce, "nonce")
    except BindingError:
        return False
    if not hmac.compare_digest(context_bytes, expected_context):
        return False
    if not isinstance(envelope.binding_tag, (bytes, bytearray)):
        return False
    if len(envelope.binding_tag) != 32:
        return False
    if envelope.nullifier is not None:
        if not isinstance(envelope.nullifier, (bytes, bytearray)):
            return False
        if len(envelope.nullifier) != 32:
            return False
    if not isinstance(envelope.public_inputs, dict):
        return False

    try:
        expected_binding_tag = compute_binding_tag(
            envelope.protocol_version,
            envelope.statement_id,
            context_bytes,
            nonce_bytes,
            envelope.public_inputs,
        )
    except BindingError:
        return False

    return hmac.compare_digest(expected_binding_tag, bytes(envelope.binding_tag))


def verify_proof(adapter: ProofAdapter, envelope: ProofEnvelope) -> bool:
    if adapter is None:
        return False
    return adapter.verify(envelope)


def verify(
    envelope: ProofEnvelope,
    expected_context_id: bytes,
    expected_statement_id: str,
    adapter: ProofAdapter,
    expected_protocol_version: str = PROTOCOL_VERSION,
) -> bool:
    return verify_envelope(
        envelope,
        expected_context_id,
        expected_statement_id,
        expected_protocol_version,
    ) and verify_proof(adapter, envelope)
