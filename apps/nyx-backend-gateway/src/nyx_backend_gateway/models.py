from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GatewayResult:
    run_id: str
    state_hash: str
    receipt_hashes: list[str]
    replay_ok: bool
