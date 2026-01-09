from __future__ import annotations

import json
from typing import Any


class CanonicalizationError(ValueError):
    pass


def canonicalize(value: object) -> bytes:
    normalized = _normalize(value)
    encoded = json.dumps(
        normalized,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return encoded.encode("utf-8")


def _normalize(value: object) -> Any:
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
        return [_normalize(item) for item in value]
    if isinstance(value, dict):
        normalized: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise CanonicalizationError("dict keys must be strings")
            _reject_surrogates(key)
            if key in normalized:
                raise CanonicalizationError("duplicate dict key")
            normalized[key] = _normalize(item)
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
