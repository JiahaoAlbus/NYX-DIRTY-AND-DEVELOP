import os
import random
import sys
from pathlib import Path
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_DIRS = [
    REPO_ROOT / "packages" / "l3-router" / "src",
    REPO_ROOT / "packages" / "l3-dex" / "src",
]
for path in SRC_DIRS:
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from l3_dex.actions import Swap  # noqa: E402
from l3_dex.state import DexState, PoolState  # noqa: E402
from l3_router.actions import RouteSwap, RouterAction, RouterActionKind  # noqa: E402
from l3_router.kernel import apply_route  # noqa: E402
from l3_router.replay import replay_route  # noqa: E402
from l3_router.state import RouterState, state_hash  # noqa: E402

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
