from __future__ import annotations

import hashlib
from pathlib import Path
import sys

from nyx_backend_gateway.env import get_fee_address
from nyx_backend_gateway.storage import FeeLedger


class FeeRoutingError(ValueError):
    pass


def _repo_root() -> Path:
    path = Path(__file__).resolve()
    for _ in range(5):
        path = path.parent
    return path


def _ensure_fee_paths() -> None:
    repo_root = _repo_root()
    paths = [
        repo_root / "packages" / "l2-economics" / "src",
        repo_root / "packages" / "l2-platform-fee" / "src",
    ]
    for path in paths:
        path_str = str(path)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)


def _fee_id(run_id: str) -> str:
    digest = hashlib.sha256(f"fee:{run_id}".encode("utf-8")).hexdigest()
    return f"fee-{digest[:16]}"


def route_fee(module: str, action: str, payload: dict[str, object], run_id: str) -> FeeLedger:
    _ensure_fee_paths()
    from action import ActionDescriptor, ActionKind
    from engine import FeeEngineV0
    from l2_platform_fee.fee_hook import enforce_platform_fee, quote_platform_fee

    action_desc = ActionDescriptor(
        kind=ActionKind.STATE_MUTATION,
        module=module,
        action=action,
        payload=payload,
    )
    engine = FeeEngineV0()
    payer = "testnet-payer"
    platform_amount = 1
    quote = quote_platform_fee(engine, action_desc, payer, platform_fee_amount=platform_amount)
    receipt = enforce_platform_fee(
        engine,
        quote,
        paid_protocol_vector=quote.protocol_quote.fee_vector,
        paid_platform_amount=quote.platform_fee_amount,
        payer=quote.payer,
    )
    fee_address = get_fee_address()
    return FeeLedger(
        fee_id=_fee_id(run_id),
        module=module,
        action=action,
        protocol_fee_total=quote.protocol_quote.fee_vector.total(),
        platform_fee_amount=quote.platform_fee_amount,
        total_paid=receipt.total_paid,
        fee_address=fee_address,
        run_id=run_id,
    )
