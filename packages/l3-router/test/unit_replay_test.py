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
