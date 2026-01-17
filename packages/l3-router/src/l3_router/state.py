from __future__ import annotations

from dataclasses import dataclass

from l3_dex.state import DexState


@dataclass(frozen=True)
class RouterState:
    dex_state: DexState
