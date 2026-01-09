from __future__ import annotations

from dataclasses import dataclass

from binding import BindingError, PROTOCOL_VERSION, compute_binding_tag, require_bytes32


class EnvelopeError(ValueError):
    pass


@dataclass(frozen=True)
class ProofEnvelope:
    protocol_version: str
    statement_id: str
    context_id: bytes
    nonce: bytes
    public_inputs: dict
    proof_bytes: bytes
    binding_tag: bytes
    nullifier: bytes | None = None


def create_envelope(
    *,
    protocol_version: str,
    statement_id: str,
    context_id: bytes,
    nonce: bytes,
    public_inputs: dict,
    proof_bytes: bytes,
    nullifier: bytes | None = None,
) -> ProofEnvelope:
    if not isinstance(proof_bytes, (bytes, bytearray)):
        raise EnvelopeError("proof_bytes must be bytes")
    if nullifier is not None and not isinstance(nullifier, (bytes, bytearray)):
        raise EnvelopeError("nullifier must be bytes")
    if nullifier is not None and len(nullifier) != 32:
        raise EnvelopeError("nullifier must be 32 bytes")

    try:
        context_bytes = require_bytes32(context_id, "context_id")
        nonce_bytes = require_bytes32(nonce, "nonce")
        binding_tag = compute_binding_tag(
            protocol_version,
            statement_id,
            context_bytes,
            nonce_bytes,
            public_inputs,
        )
    except BindingError as exc:
        raise EnvelopeError(str(exc)) from exc

    return ProofEnvelope(
        protocol_version=protocol_version,
        statement_id=statement_id,
        context_id=context_bytes,
        nonce=nonce_bytes,
        public_inputs=public_inputs,
        proof_bytes=bytes(proof_bytes),
        binding_tag=binding_tag,
        nullifier=bytes(nullifier) if nullifier is not None else None,
    )


def create_default_envelope(
    *,
    statement_id: str,
    context_id: bytes,
    nonce: bytes,
    public_inputs: dict,
    proof_bytes: bytes,
    nullifier: bytes | None = None,
) -> ProofEnvelope:
    return create_envelope(
        protocol_version=PROTOCOL_VERSION,
        statement_id=statement_id,
        context_id=context_id,
        nonce=nonce,
        public_inputs=public_inputs,
        proof_bytes=proof_bytes,
        nullifier=nullifier,
    )
