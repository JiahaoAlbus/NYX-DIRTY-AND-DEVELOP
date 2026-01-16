from __future__ import annotations

from .receipts import RouterReceipt
from .state import RouterState


def replay_route(state: RouterState, receipt: RouterReceipt) -> RouterState:
    raise NotImplementedError("router replay is implemented in later weeks")
