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
from l3_router.errors import ValidationError  # noqa: E402
from l3_router.kernel import apply_route  # noqa: E402
from l3_router.state import RouterState, state_hash  # noqa: E402


class AtomicFailureTests(unittest.TestCase):
    def test_failure_keeps_state_unchanged(self) -> None:
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
        original_hash = state_hash(state.dex_state)

        steps = (
            Swap(pool_id="pool-1", amount_in=10, min_out=0, asset_in="ASSET_A"),
            Swap(pool_id="missing", amount_in=10, min_out=0, asset_in="ASSET_A"),
        )
        action = RouterAction(kind=RouterActionKind.ROUTE_SWAP, payload=RouteSwap(steps=steps))

        with self.assertRaises(ValidationError):
            apply_route(state, action)

        self.assertEqual(state_hash(state.dex_state), original_hash)


if __name__ == "__main__":
    unittest.main()
