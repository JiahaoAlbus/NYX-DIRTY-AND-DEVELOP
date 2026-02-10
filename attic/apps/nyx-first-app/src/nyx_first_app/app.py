from __future__ import annotations

from pathlib import Path

from e2e_demo.pipeline import run_e2e
from e2e_demo.replay import replay_and_verify

from nyx_first_app.models import AppConfig, AppError, AppSummary


def run_app(seed: int, out_path: str, action: str = "post_note") -> AppSummary:
    config = AppConfig(seed=seed, out_path=out_path, action=action)

    trace, summary = run_e2e(seed=config.seed)
    replay = replay_and_verify(trace)
    if not replay.ok:
        raise AppError("trace replay failed")

    out_file = Path(config.out_path)
    out_file.write_text(trace.to_json(), encoding="utf-8")

    return AppSummary(
        action=config.action,
        fee_total=summary.fee_total,
        tx_hash_prefix=summary.tx_hash_prefix,
        block_hash_prefix=summary.block_hash_prefix,
        state_root_prefix=summary.state_root_prefix,
        receipt_hash_prefix=summary.receipt_hash_prefix,
        replay_ok=replay.ok,
    )
