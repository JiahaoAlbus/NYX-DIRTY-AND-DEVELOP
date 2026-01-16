from __future__ import annotations

import argparse
import json
from pathlib import Path

from nyx_reference_client.app import run_client


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="NYX reference client")
    parser.add_argument("--seed", type=int, default=123, help="Deterministic seed")
    parser.add_argument("--steps", type=int, default=2, help="Route step count")
    parser.add_argument("--out", required=True, help="Report output path")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    summary = run_client(seed=args.seed, out_path=args.out, steps=args.steps)
    report = json.loads(Path(args.out).read_text(encoding="utf-8"))

    print(
        "summary:"
        f" state_hash={summary.state_hash_hex}"
        f" receipt_chain={summary.receipt_chain_hex}"
        f" replay_ok={summary.replay_ok}"
    )

    for idx, entry in enumerate(report.get("step_panel", []), start=1):
        print(
            "step:"
            f" index={idx}"
            f" pool_id={entry.get('pool_id')}"
            f" asset_in={entry.get('asset_in')}"
            f" amount_in={entry.get('amount_in')}"
            f" amount_out={entry.get('amount_out')}"
            f" reserve_a={entry.get('reserve_a')}"
            f" reserve_b={entry.get('reserve_b')}"
            f" total_lp={entry.get('total_lp')}"
            f" fee_charged={entry.get('fee_charged')}"
        )


if __name__ == "__main__":
    main()
