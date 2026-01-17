from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Iterable

from l3_dex.state import DexState, PoolState

from .errors import ValidationError

_MAX_DEPTH = 20
_MAX_BYTES = 65536


@dataclass(frozen=True)
class RouterState:
    dex_state: DexState


def _sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def _assert_json_types(value, depth: int = 0) -> None:
    if depth > _MAX_DEPTH:
        raise ValidationError("max depth exceeded")
    if value is None or isinstance(value, str) or isinstance(value, bool):
        return
    if isinstance(value, int) and not isinstance(value, bool):
        return
    if isinstance(value, list) or isinstance(value, tuple):
        for item in value:
            _assert_json_types(item, depth + 1)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValidationError("dict keys must be str")
            _assert_json_types(item, depth + 1)
        return
    raise ValidationError("unsupported type")


def _canonical_bytes(value) -> bytes:
    _assert_json_types(value)
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    data = raw.encode("utf-8")
    if len(data) > _MAX_BYTES:
        raise ValidationError("max bytes exceeded")
    return data


def _pool_to_dict(pool: PoolState) -> dict:
    return {
        "pool_id": pool.pool_id,
        "asset_a": pool.asset_a,
        "asset_b": pool.asset_b,
        "reserve_a": pool.reserve_a,
        "reserve_b": pool.reserve_b,
        "total_lp": pool.total_lp,
    }


def _sorted_pools(state: DexState) -> Iterable[PoolState]:
    return tuple(sorted(state.pools, key=lambda pool: pool.pool_id))


def state_hash(state: DexState) -> bytes:
    payload = {
        "pools": [_pool_to_dict(pool) for pool in _sorted_pools(state)],
    }
    return _sha256(_canonical_bytes(payload))
