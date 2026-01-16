from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from l3_dex.actions import Swap as DexSwap
from l3_dex.receipts import DexReceipt

from .actions import RouterActionKind


@dataclass(frozen=True)
class RouterReceipt:
    action: RouterActionKind
    state_hash: bytes
    steps: Tuple[DexSwap, ...]
    step_receipts: Tuple[DexReceipt, ...]
