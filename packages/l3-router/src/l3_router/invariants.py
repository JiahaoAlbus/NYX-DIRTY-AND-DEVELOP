from __future__ import annotations

from l3_dex.invariants import check_invariants as check_dex_invariants

from .state import RouterState


def check_invariants(state: RouterState) -> None:
    check_dex_invariants(state.dex_state)
