from __future__ import annotations

import json
from typing import Any


MAX_CANONICAL_DEPTH = 64
MAX_CANONICAL_BYTES = 1_048_576


class CanonicalizationError(ValueError):
    pass


def canonicalize(
    value: object,
    *,
    max_depth: int = MAX_CANONICAL_DEPTH,
    max_bytes: int = MAX_CANONICAL_BYTES,
) -> bytes:
    if not isinstance(max_depth, int) or max_depth < 1:
        raise CanonicalizationError("max_depth must be a positive integer")
    if not isinstance(max_bytes, int) or max_bytes < 1:
        raise CanonicalizationError("max_bytes must be a positive integer")
    normalized = _normalize(value, depth=0, max_depth=max_depth)
    encoded = json.dumps(
        normalized,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    if len(encoded) > max_bytes:
        raise CanonicalizationError("canonical output exceeds max bytes")
    return encoded


def _normalize(value: object, *, depth: int, max_depth: int) -> Any:
    if depth > max_depth:
        raise CanonicalizationError("maximum canonical depth exceeded")
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, str):
        _reject_surrogates(value)
        return value
    if isinstance(value, (list, tuple)):
        return [_normalize(item, depth=depth + 1, max_depth=max_depth) for item in value]
    if isinstance(value, dict):
        normalized: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise CanonicalizationError("dict keys must be strings")
            _reject_surrogates(key)
            if key in normalized:
                raise CanonicalizationError("duplicate dict key")
            normalized[key] = _normalize(item, depth=depth + 1, max_depth=max_depth)
        return normalized
    if isinstance(value, float):
        raise CanonicalizationError("float values are not permitted")
    if isinstance(value, (bytes, bytearray)):
        raise CanonicalizationError("byte values are not permitted")
    if isinstance(value, set):
        raise CanonicalizationError("set values are not permitted")
    raise CanonicalizationError(f"unsupported type: {type(value).__name__}")


def _reject_surrogates(text: str) -> None:
    for char in text:
        code = ord(char)
        if 0xD800 <= code <= 0xDFFF:
            raise CanonicalizationError("surrogate code points are not permitted")
