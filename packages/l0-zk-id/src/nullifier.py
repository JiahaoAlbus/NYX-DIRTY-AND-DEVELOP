from __future__ import annotations

import hashlib

from binding import BindingError, require_bytes32

NULLIFIER_DOMAIN = b"NYX:ZKID:NULLIFIER:v1"


class NullifierError(ValueError):
    pass


def compute_nullifier(
    *,
    context_id: bytes,
    statement_id: str,
    epoch_or_nonce: bytes,
    secret_commitment: bytes,
) -> bytes:
    try:
        context_bytes = require_bytes32(context_id, "context_id")
        epoch_bytes = require_bytes32(epoch_or_nonce, "epoch_or_nonce")
        secret_bytes = require_bytes32(secret_commitment, "secret_commitment")
    except BindingError as exc:
        raise NullifierError(str(exc)) from exc
    if not isinstance(statement_id, str) or not statement_id:
        raise NullifierError("statement_id must be a non-empty string")
    _reject_surrogates(statement_id)

    payload = b"".join(
        [
            NULLIFIER_DOMAIN,
            context_bytes,
            statement_id.encode("utf-8"),
            epoch_bytes,
            secret_bytes,
        ]
    )
    return hashlib.sha256(payload).digest()


def _reject_surrogates(text: str) -> None:
    for char in text:
        code = ord(char)
        if 0xD800 <= code <= 0xDFFF:
            raise NullifierError("surrogate code points are not permitted")
