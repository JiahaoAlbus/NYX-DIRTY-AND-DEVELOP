from __future__ import annotations

import hmac

from .actions import RouteSwap, RouterAction
from .errors import ReplayError
from .kernel import apply_route
from .receipts import RouterReceipt
from .state import RouterState


def replay_route(state: RouterState, receipt: RouterReceipt) -> RouterState:
    action = RouterAction(kind=receipt.action, payload=RouteSwap(steps=receipt.steps))
    next_state, computed = apply_route(state, action)

    if not hmac.compare_digest(computed.state_hash, receipt.state_hash):
        raise ReplayError("state hash mismatch")

    if len(computed.step_receipts) != len(receipt.step_receipts):
        raise ReplayError("step receipt length mismatch")

    for expected, actual in zip(receipt.step_receipts, computed.step_receipts, strict=True):
        if expected.action != actual.action:
            raise ReplayError("step action mismatch")
        if expected.pool_id != actual.pool_id:
            raise ReplayError("step pool mismatch")
        if not hmac.compare_digest(expected.state_hash, actual.state_hash):
            raise ReplayError("step hash mismatch")

    return next_state
