from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from l3_dex.receipts import DexReceipt

from .actions import RouterActionKind


@dataclass(frozen=True)
class RouterReceipt:
    action: RouterActionKind
    state_hash: bytes
    step_receipts: Tuple[DexReceipt, ...]
