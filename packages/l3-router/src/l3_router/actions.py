from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Tuple

from l3_dex.actions import Swap as DexSwap


class RouterActionKind(str, Enum):
    ROUTE_SWAP = "ROUTE_SWAP"


@dataclass(frozen=True)
class RouteSwap:
    steps: Tuple[DexSwap, ...]


@dataclass(frozen=True)
class RouterAction:
    kind: RouterActionKind
    payload: RouteSwap
