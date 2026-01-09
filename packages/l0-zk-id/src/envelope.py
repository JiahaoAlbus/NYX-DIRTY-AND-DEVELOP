from __future__ import annotations

from dataclasses import dataclass

from binding import BindingError, PROTOCOL_VERSION, compute_binding_tag
from canonical import CanonicalizationError, canonicalize


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

    def __post_init__(self) -> None:
        _require_text(self.protocol_version, "protocol_version")
        _require_text(self.statement_id, "statement_id")
        _require_bytes32(self.context_id, "context_id")
        _require_bytes32(self.nonce, "nonce")
        _require_bytes32(self.binding_tag, "binding_tag")
        if not isinstance(self.proof_bytes, bytes):
            raise EnvelopeError("proof_bytes must be bytes")
        if self.nullifier is not None:
            _require_bytes32(self.nullifier, "nullifier")
        _require_public_inputs(self.public_inputs)


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
    _require_text(protocol_version, "protocol_version")
    _require_text(statement_id, "statement_id")
    _require_bytes32(context_id, "context_id")
    _require_bytes32(nonce, "nonce")
    _require_public_inputs(public_inputs)
    if not isinstance(proof_bytes, bytes):
        raise EnvelopeError("proof_bytes must be bytes")
    if nullifier is not None:
        _require_bytes32(nullifier, "nullifier")

    try:
        binding_tag = compute_binding_tag(
            protocol_version,
            statement_id,
            context_id,
            nonce,
            public_inputs,
        )
    except BindingError as exc:
        raise EnvelopeError(str(exc)) from exc

    return ProofEnvelope(
        protocol_version=protocol_version,
        statement_id=statement_id,
        context_id=context_id,
        nonce=nonce,
        public_inputs=public_inputs,
        proof_bytes=proof_bytes,
        binding_tag=binding_tag,
        nullifier=nullifier,
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


def _require_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise EnvelopeError(f"{field_name} must be a string")
    if not value:
        raise EnvelopeError(f"{field_name} must be non-empty")
    _reject_surrogates(value)
    return value


def _require_bytes32(value: object, field_name: str) -> bytes:
    if not isinstance(value, bytes):
        raise EnvelopeError(f"{field_name} must be 32 bytes")
    if len(value) != 32:
        raise EnvelopeError(f"{field_name} must be 32 bytes")
    return value


def _require_public_inputs(value: object) -> None:
    if not isinstance(value, dict):
        raise EnvelopeError("public_inputs must be a dict")
    try:
        canonicalize(value)
    except CanonicalizationError as exc:
        raise EnvelopeError(str(exc)) from exc


def _reject_surrogates(text: str) -> None:
    for char in text:
        code = ord(char)
        if 0xD800 <= code <= 0xDFFF:
            raise EnvelopeError("surrogate code points are not permitted")
