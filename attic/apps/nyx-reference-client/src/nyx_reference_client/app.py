from __future__ import annotations

import hashlib
import hmac
import json
import random
from pathlib import Path
from typing import Iterable

from l3_dex.actions import Swap as DexSwap
from l3_dex.receipts import DexReceipt
from l3_dex.state import DexState, PoolState
from l3_router.actions import RouteSwap, RouterAction, RouterActionKind
from l3_router.kernel import apply_route, route_state_hash
from l3_router.receipts import RouterReceipt
from l3_router.replay import replay_route
from l3_router.state import RouterState

from nyx_reference_client.models import (
    ClientConfig,
    ClientReport,
    ClientSummary,
    PoolSnapshot,
    RouteStepView,
    StepResult,
)

_MAX_STEPS = 8
_MAX_DEPTH = 20
_MAX_BYTES = 65536

_POOL_ID = "pool-0"
_ASSET_A = "ASSET_A"
_ASSET_B = "ASSET_B"
_BASE_RESERVE_A = 1_000_000
_BASE_RESERVE_B = 2_000_000
_BASE_TOTAL_LP = 3_000_000


class ClientError(ValueError):
    pass


def _sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def _framed(parts: Iterable[bytes]) -> bytes:
    out = bytearray()
    for part in parts:
        out.extend(len(part).to_bytes(4, "big"))
        out.extend(part)
    return bytes(out)


def _assert_json_types(value, depth: int = 0) -> None:
    if depth > _MAX_DEPTH:
        raise ClientError("max depth exceeded")
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
                raise ClientError("dict keys must be str")
            _assert_json_types(item, depth + 1)
        return
    raise ClientError("unsupported type")


def _canonical_bytes(value) -> bytes:
    _assert_json_types(value)
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    data = raw.encode("utf-8")
    if len(data) > _MAX_BYTES:
        raise ClientError("max bytes exceeded")
    return data


def _build_initial_state() -> tuple[RouterState, PoolSnapshot]:
    pool = PoolState(
        pool_id=_POOL_ID,
        asset_a=_ASSET_A,
        asset_b=_ASSET_B,
        reserve_a=_BASE_RESERVE_A,
        reserve_b=_BASE_RESERVE_B,
        total_lp=_BASE_TOTAL_LP,
    )
    snapshot = PoolSnapshot(
        pool_id=pool.pool_id,
        asset_a=pool.asset_a,
        asset_b=pool.asset_b,
        reserve_a=pool.reserve_a,
        reserve_b=pool.reserve_b,
        total_lp=pool.total_lp,
    )
    return RouterState(dex_state=DexState(pools=(pool,))), snapshot


def _build_route(seed: int, steps: int) -> tuple[RouteStepView, ...]:
    rng = random.Random(seed)
    route_steps: list[RouteStepView] = []
    for _ in range(steps):
        amount_in = rng.randint(1, 1000)
        asset_in = _ASSET_A if rng.randint(0, 1) == 0 else _ASSET_B
        route_steps.append(
            RouteStepView(
                pool_id=_POOL_ID,
                asset_in=asset_in,
                amount_in=amount_in,
                min_out=0,
            )
        )
    return tuple(route_steps)


def _steps_to_swaps(steps: tuple[RouteStepView, ...]) -> tuple[DexSwap, ...]:
    return tuple(
        DexSwap(
            pool_id=step.pool_id,
            amount_in=step.amount_in,
            min_out=step.min_out,
            asset_in=step.asset_in,
        )
        for step in steps
    )


def _route_action(steps: tuple[RouteStepView, ...]) -> RouterAction:
    swaps = _steps_to_swaps(steps)
    return RouterAction(kind=RouterActionKind.ROUTE_SWAP, payload=RouteSwap(steps=swaps))


def _find_pool(state: DexState, pool_id: str) -> PoolState | None:
    for pool in state.pools:
        if pool.pool_id == pool_id:
            return pool
    return None


def _step_panel(state: RouterState, steps: tuple[RouteStepView, ...]) -> tuple[StepResult, ...]:
    current = state
    panel: list[StepResult] = []
    for step in steps:
        before = _find_pool(current.dex_state, step.pool_id)
        if before is None:
            raise ClientError("pool missing")
        action = RouterAction(
            kind=RouterActionKind.ROUTE_SWAP,
            payload=RouteSwap(steps=_steps_to_swaps((step,))),
        )
        next_state, _ = apply_route(current, action)
        after = _find_pool(next_state.dex_state, step.pool_id)
        if after is None:
            raise ClientError("pool missing")
        if step.asset_in == before.asset_a:
            amount_out = before.reserve_b - after.reserve_b
        else:
            amount_out = before.reserve_a - after.reserve_a
        panel.append(
            StepResult(
                pool_id=step.pool_id,
                asset_in=step.asset_in,
                amount_in=step.amount_in,
                amount_out=amount_out,
                reserve_a=after.reserve_a,
                reserve_b=after.reserve_b,
                total_lp=after.total_lp,
                fee_charged=0,
            )
        )
        current = next_state
    return tuple(panel)


def _dex_receipt_hash(receipt: DexReceipt) -> bytes:
    payload = {
        "action": receipt.action.value,
        "pool_id": receipt.pool_id,
        "state_hash": receipt.state_hash.hex(),
    }
    return _sha256(_canonical_bytes(payload))


def _receipt_chain_hash(receipt: RouterReceipt) -> bytes:
    hashes = [_dex_receipt_hash(step) for step in receipt.step_receipts]
    return _sha256(_framed(hashes))


def replay_and_verify(report: ClientReport) -> bool:
    pool = report.pool
    initial = RouterState(
        dex_state=DexState(
            pools=(
                PoolState(
                    pool_id=pool.pool_id,
                    asset_a=pool.asset_a,
                    asset_b=pool.asset_b,
                    reserve_a=pool.reserve_a,
                    reserve_b=pool.reserve_b,
                    total_lp=pool.total_lp,
                ),
            )
        )
    )
    action = _route_action(report.steps)
    final_state, receipt = apply_route(initial, action)
    state_hash = route_state_hash(final_state)
    receipt_chain = _receipt_chain_hash(receipt)

    if not hmac.compare_digest(state_hash, bytes.fromhex(report.state_hash_hex)):
        return False
    if not hmac.compare_digest(receipt_chain, bytes.fromhex(report.receipt_chain_hex)):
        return False

    try:
        replay_state = replay_route(initial, receipt)
    except Exception:
        return False

    return hmac.compare_digest(route_state_hash(replay_state), receipt.state_hash)


def run_client(seed: int, out_path: str, steps: int = 2) -> ClientSummary:
    if steps < 1 or steps > _MAX_STEPS:
        raise ClientError("steps out of bounds")

    config = ClientConfig(seed=seed, steps=steps, out_path=out_path)
    initial_state, pool_snapshot = _build_initial_state()
    route_steps = _build_route(config.seed, config.steps)

    action = _route_action(route_steps)
    final_state, receipt = apply_route(initial_state, action)
    state_hash = route_state_hash(final_state)
    if not hmac.compare_digest(state_hash, receipt.state_hash):
        raise ClientError("state hash mismatch")

    step_panel = _step_panel(initial_state, route_steps)
    receipt_chain = _receipt_chain_hash(receipt)

    report = ClientReport(
        pool=pool_snapshot,
        steps=route_steps,
        step_panel=step_panel,
        state_hash_hex=state_hash.hex(),
        receipt_chain_hex=receipt_chain.hex(),
    )

    replay_ok = replay_and_verify(report)

    out_file = Path(config.out_path)
    out_file.write_text(
        json.dumps(report.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=True),
        encoding="utf-8",
    )

    return ClientSummary(
        state_hash_hex=report.state_hash_hex,
        receipt_chain_hex=report.receipt_chain_hex,
        replay_ok=replay_ok,
    )
