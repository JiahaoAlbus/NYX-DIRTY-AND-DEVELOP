import os
import random
import unittest

from l3_dex.actions import Swap
from l3_dex.state import DexState, PoolState
from l3_router.actions import RouteSwap, RouterAction, RouterActionKind
from l3_router.kernel import apply_route
from l3_router.replay import replay_route
from l3_router.state import RouterState, state_hash

PROPERTY_N = int(os.getenv("PROPERTY_N", "2000"))


class RouterPropertyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        print(f"PROPERTY_N={PROPERTY_N}")

    def test_invariants(self) -> None:
        rng = random.Random(2024)
        for _ in range(PROPERTY_N):
            reserve_a = rng.randint(1000, 100000)
            reserve_b = rng.randint(1000, 100000)
            pool = PoolState(
                pool_id="pool-1",
                asset_a="ASSET_A",
                asset_b="ASSET_B",
                reserve_a=reserve_a,
                reserve_b=reserve_b,
                total_lp=reserve_a + reserve_b,
            )
            state = RouterState(dex_state=DexState(pools=(pool,)))

            asset_in = "ASSET_A" if rng.randint(0, 1) == 0 else "ASSET_B"
            reserve_in = reserve_a if asset_in == "ASSET_A" else reserve_b
            reserve_out = reserve_b if asset_in == "ASSET_A" else reserve_a

            amount_in = rng.randint(1, 1000)
            if (reserve_out * amount_in) // (reserve_in + amount_in) == 0:
                amount_in = reserve_in // reserve_out + 1

            step = Swap(
                pool_id="pool-1",
                amount_in=amount_in,
                min_out=0,
                asset_in=asset_in,
            )
            action = RouterAction(
                kind=RouterActionKind.ROUTE_SWAP,
                payload=RouteSwap(steps=(step,)),
            )

            new_state, receipt = apply_route(state, action)
            pool_after = new_state.dex_state.pools[0]
            self.assertGreaterEqual(pool_after.reserve_a, 0)
            self.assertGreaterEqual(pool_after.reserve_b, 0)
            self.assertEqual(state_hash(new_state.dex_state), receipt.state_hash)

            replayed = replay_route(state, receipt)
            self.assertEqual(state_hash(replayed.dex_state), receipt.state_hash)


if __name__ == "__main__":
    unittest.main()
