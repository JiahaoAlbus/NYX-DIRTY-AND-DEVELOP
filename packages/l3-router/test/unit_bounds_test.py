import unittest

from l3_dex.actions import Swap
from l3_dex.state import DexState, PoolState
from l3_router.actions import RouteSwap, RouterAction, RouterActionKind
from l3_router.errors import ValidationError
from l3_router.kernel import apply_route
from l3_router.state import RouterState

_MAX_AMOUNT = 10**12
_MAX_STEPS = 8
_MAX_RESERVE = 10**18


class BoundsTests(unittest.TestCase):
    def _base_state(self) -> RouterState:
        return RouterState(
            dex_state=DexState(
                pools=(
                    PoolState(
                        pool_id="pool-1",
                        asset_a="ASSET_A",
                        asset_b="ASSET_B",
                        reserve_a=1000,
                        reserve_b=1000,
                        total_lp=1000,
                    ),
                ),
            )
        )

    def test_amount_in_too_large(self) -> None:
        state = self._base_state()
        step = Swap(
            pool_id="pool-1",
            amount_in=_MAX_AMOUNT + 1,
            min_out=0,
            asset_in="ASSET_A",
        )
        action = RouterAction(
            kind=RouterActionKind.ROUTE_SWAP,
            payload=RouteSwap(steps=(step,)),
        )
        with self.assertRaises(ValidationError):
            apply_route(state, action)

    def test_min_out_too_large(self) -> None:
        state = self._base_state()
        step = Swap(
            pool_id="pool-1",
            amount_in=10,
            min_out=_MAX_AMOUNT + 1,
            asset_in="ASSET_A",
        )
        action = RouterAction(
            kind=RouterActionKind.ROUTE_SWAP,
            payload=RouteSwap(steps=(step,)),
        )
        with self.assertRaises(ValidationError):
            apply_route(state, action)

    def test_steps_too_many(self) -> None:
        state = self._base_state()
        steps = tuple(
            Swap(
                pool_id="pool-1",
                amount_in=10,
                min_out=0,
                asset_in="ASSET_A",
            )
            for _ in range(_MAX_STEPS + 1)
        )
        action = RouterAction(
            kind=RouterActionKind.ROUTE_SWAP,
            payload=RouteSwap(steps=steps),
        )
        with self.assertRaises(ValidationError):
            apply_route(state, action)

    def test_reserve_too_large(self) -> None:
        state = RouterState(
            dex_state=DexState(
                pools=(
                    PoolState(
                        pool_id="pool-1",
                        asset_a="ASSET_A",
                        asset_b="ASSET_B",
                        reserve_a=_MAX_RESERVE + 1,
                        reserve_b=1000,
                        total_lp=1000,
                    ),
                ),
            )
        )
        step = Swap(
            pool_id="pool-1",
            amount_in=10,
            min_out=0,
            asset_in="ASSET_A",
        )
        action = RouterAction(
            kind=RouterActionKind.ROUTE_SWAP,
            payload=RouteSwap(steps=(step,)),
        )
        with self.assertRaises(ValidationError):
            apply_route(state, action)


if __name__ == "__main__":
    unittest.main()
