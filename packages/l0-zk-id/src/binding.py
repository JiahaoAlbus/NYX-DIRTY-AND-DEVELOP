from __future__ import annotations

import hashlib

from canonical import CanonicalizationError, canonicalize

DOMAIN_TAG = b"NYX:ZKID:PROOF_ENVELOPE:v1"
PROTOCOL_VERSION = "NYX-ZKID/0.1"
BINDING_TAG_BYTES = 32


class BindingError(ValueError):
    pass


def compute_binding_tag(
    protocol_version: str,
    statement_id: str,
    context_id: bytes,
    nonce: bytes,
    public_inputs: dict,
) -> bytes:
    if not isinstance(public_inputs, dict):
        raise BindingError("public_inputs must be a dict")
    protocol_bytes = _len_prefix(_require_text(protocol_version, "protocol_version"))
    statement_bytes = _len_prefix(_require_text(statement_id, "statement_id"))
    context_bytes = require_bytes32(context_id, "context_id")
    nonce_bytes = require_bytes32(nonce, "nonce")
    try:
        public_inputs_bytes = canonicalize(public_inputs)
    except CanonicalizationError as exc:
        raise BindingError(str(exc)) from exc

    payload = b"".join(
        [
            DOMAIN_TAG,
            protocol_bytes,
            statement_bytes,
            context_bytes,
            nonce_bytes,
            public_inputs_bytes,
        ]
    )
    return hashlib.sha256(payload).digest()


def require_bytes32(value: object, field_name: str) -> bytes:
    if isinstance(value, str):
        return _parse_hex_bytes32(value, field_name)
    if not isinstance(value, (bytes, bytearray)):
        raise BindingError(f"{field_name} must be 32 bytes")
    data = bytes(value)
    if len(data) != 32:
        raise BindingError(f"{field_name} must be 32 bytes")
    return data


def _require_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise BindingError(f"{field_name} must be a string")
    if not value:
        raise BindingError(f"{field_name} must be non-empty")
    _reject_surrogates(value)
    return value


def _len_prefix(text: str) -> bytes:
    data = text.encode("utf-8")
    if len(data) > 0xFFFFFFFF:
        raise BindingError("text field too large")
    return len(data).to_bytes(4, "big") + data


def _parse_hex_bytes32(value: str, field_name: str) -> bytes:
    if value.startswith("0x"):
        value = value[2:]
    if len(value) != 64:
        raise BindingError(f"{field_name} must be 32 bytes")
    try:
        data = bytes.fromhex(value)
    except ValueError as exc:
        raise BindingError(f"{field_name} must be hex") from exc
    if len(data) != 32:
        raise BindingError(f"{field_name} must be 32 bytes")
    return data


def _reject_surrogates(text: str) -> None:
    for char in text:
        code = ord(char)
        if 0xD800 <= code <= 0xDFFF:
            raise BindingError("surrogate code points are not permitted")
