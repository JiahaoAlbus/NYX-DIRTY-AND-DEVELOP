from __future__ import annotations

from dataclasses import replace
from typing import Iterable

from l3_dex.actions import ActionKind, Swap as DexSwap
from l3_dex.receipts import DexReceipt
from l3_dex.state import DexState, PoolState

from .actions import RouterAction, RouterActionKind
from .errors import ValidationError
from .receipts import RouterReceipt
from .state import RouterState, state_hash

_MAX_STEPS = 8
_MAX_AMOUNT = 10**12
_MAX_RESERVE = 10**18


def _find_pool(state: DexState, pool_id: str) -> PoolState | None:
    for pool in state.pools:
        if pool.pool_id == pool_id:
            return pool
    return None


def _replace_pool(state: DexState, updated: PoolState) -> DexState:
    pools = tuple(pool for pool in state.pools if pool.pool_id != updated.pool_id)
    return DexState(pools=pools + (updated,))


def _check_amount(value: int, name: str) -> None:
    if value < 0:
        raise ValidationError(f"{name} must be non-negative")
    if value > _MAX_AMOUNT:
        raise ValidationError(f"{name} exceeds max")


def _check_reserve(value: int, name: str) -> None:
    if value < 0:
        raise ValidationError(f"{name} must be non-negative")
    if value > _MAX_RESERVE:
        raise ValidationError(f"{name} exceeds max")


def _apply_swap(state: DexState, step: DexSwap) -> DexState:
    if step.amount_in <= 0:
        raise ValidationError("amount_in must be positive")
    _check_amount(step.amount_in, "amount_in")
    _check_amount(step.min_out, "min_out")

    pool = _find_pool(state, step.pool_id)
    if pool is None:
        raise ValidationError("pool missing")

    _check_reserve(pool.reserve_a, "reserve_a")
    _check_reserve(pool.reserve_b, "reserve_b")
    _check_reserve(pool.total_lp, "total_lp")

    if step.asset_in == pool.asset_a:
        reserve_in = pool.reserve_a
        reserve_out = pool.reserve_b
        in_is_a = True
    elif step.asset_in == pool.asset_b:
        reserve_in = pool.reserve_b
        reserve_out = pool.reserve_a
        in_is_a = False
    else:
        raise ValidationError("asset_in mismatch")

    if reserve_in <= 0 or reserve_out <= 0:
        raise ValidationError("reserves must be positive")

    if reserve_in + step.amount_in > _MAX_RESERVE:
        raise ValidationError("reserve_in exceeds max")

    amount_out = (reserve_out * step.amount_in) // (reserve_in + step.amount_in)
    if amount_out <= 0:
        raise ValidationError("amount_out is zero")
    if amount_out < step.min_out:
        raise ValidationError("min_out not met")
    if amount_out > reserve_out:
        raise ValidationError("amount_out exceeds reserve")

    if in_is_a:
        new_pool = replace(
            pool,
            reserve_a=pool.reserve_a + step.amount_in,
            reserve_b=pool.reserve_b - amount_out,
        )
    else:
        new_pool = replace(
            pool,
            reserve_a=pool.reserve_a - amount_out,
            reserve_b=pool.reserve_b + step.amount_in,
        )

    _check_reserve(new_pool.reserve_a, "reserve_a")
    _check_reserve(new_pool.reserve_b, "reserve_b")

    return _replace_pool(state, new_pool)


def apply_route(state: RouterState, action: RouterAction) -> tuple[RouterState, RouterReceipt]:
    if action.kind is not RouterActionKind.ROUTE_SWAP:
        raise ValidationError("unsupported action")

    steps = action.payload.steps
    if not steps:
        raise ValidationError("route steps empty")
    if len(steps) > _MAX_STEPS:
        raise ValidationError("route steps exceed max")

    current_state = state.dex_state
    step_receipts: list[DexReceipt] = []

    for step in steps:
        current_state = _apply_swap(current_state, step)
        step_receipts.append(
            DexReceipt(
                action=ActionKind.SWAP,
                pool_id=step.pool_id,
                state_hash=state_hash(current_state),
            )
        )

    final_hash = state_hash(current_state)
    receipt = RouterReceipt(
        action=RouterActionKind.ROUTE_SWAP,
        state_hash=final_hash,
        steps=steps,
        step_receipts=tuple(step_receipts),
    )
    return RouterState(dex_state=current_state), receipt


def route_state_hash(state: RouterState) -> bytes:
    return state_hash(state.dex_state)
