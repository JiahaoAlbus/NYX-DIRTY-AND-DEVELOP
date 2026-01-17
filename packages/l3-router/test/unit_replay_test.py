import unittest

from l3_dex.actions import Swap
from l3_dex.state import DexState, PoolState
from l3_router.actions import RouteSwap, RouterAction, RouterActionKind
from l3_router.kernel import apply_route
from l3_router.replay import replay_route
from l3_router.state import RouterState, state_hash


class ReplayTests(unittest.TestCase):
    def test_replay_matches_receipt(self) -> None:
        state = RouterState(
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

        step = Swap(pool_id="pool-1", amount_in=50, min_out=0, asset_in="ASSET_A")
        action = RouterAction(
            kind=RouterActionKind.ROUTE_SWAP,
            payload=RouteSwap(steps=(step,)),
        )
        new_state, receipt = apply_route(state, action)
        replayed_state = replay_route(state, receipt)

        self.assertEqual(state_hash(new_state.dex_state), state_hash(replayed_state.dex_state))


if __name__ == "__main__":
    unittest.main()
