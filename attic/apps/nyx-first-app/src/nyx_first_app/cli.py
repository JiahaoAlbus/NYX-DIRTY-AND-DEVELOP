from __future__ import annotations

import argparse

from nyx_first_app.app import run_app


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="NYX first app demo")
    parser.add_argument("--seed", type=int, default=123, help="Deterministic seed")
    parser.add_argument("--out", required=True, help="Trace output path")
    parser.add_argument("--action", default="post_note", help="App action label")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    summary = run_app(seed=args.seed, out_path=args.out, action=args.action)
    print(
        "summary:"
        f" action={summary.action}"
        f" fee_total={summary.fee_total}"
        f" tx_hash={summary.tx_hash_prefix}"
        f" block_hash={summary.block_hash_prefix}"
        f" state_root={summary.state_root_prefix}"
        f" receipt_hash={summary.receipt_hash_prefix}"
        f" replay_ok={summary.replay_ok}"
    )


if __name__ == "__main__":
    main()
