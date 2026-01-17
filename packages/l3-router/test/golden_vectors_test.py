import unittest

from l3_dex.actions import Swap
from l3_dex.state import DexState, PoolState
from l3_router.actions import RouteSwap, RouterAction, RouterActionKind
from l3_router.kernel import apply_route
from l3_router.state import RouterState, state_hash


class GoldenVectorTests(unittest.TestCase):
    def test_single_swap_vector(self) -> None:
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

        step = Swap(pool_id="pool-1", amount_in=100, min_out=0, asset_in="ASSET_A")
        action = RouterAction(
            kind=RouterActionKind.ROUTE_SWAP,
            payload=RouteSwap(steps=(step,)),
        )

        new_state, receipt = apply_route(state, action)
        expected = "9396c75063662f30e686cb09dcce028edad10e51a4ed96ea06aa212799cb854c"
        self.assertEqual(state_hash(new_state.dex_state).hex(), expected)
        self.assertEqual(receipt.state_hash.hex(), expected)
        self.assertEqual(receipt.step_receipts[0].state_hash.hex(), expected)
        pool = new_state.dex_state.pools[0]
        self.assertEqual(pool.reserve_a, 1100)
        self.assertEqual(pool.reserve_b, 910)


if __name__ == "__main__":
    unittest.main()
