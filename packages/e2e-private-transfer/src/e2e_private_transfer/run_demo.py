from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _add_paths() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    paths = [
        repo_root / "packages" / "e2e-private-transfer" / "src",
        repo_root / "packages" / "l2-private-ledger" / "src",
        repo_root / "packages" / "l0-zk-id" / "src",
        repo_root / "packages" / "l2-economics" / "src",
        repo_root / "packages" / "l1-chain" / "src",
        repo_root / "packages" / "wallet-kernel" / "src",
    ]
    for path in paths:
        path_str = str(path)
        if path_str in sys.path:
            sys.path.remove(path_str)
        sys.path.insert(0, path_str)


_add_paths()

from e2e_private_transfer.pipeline import run_private_transfer  # noqa: E402
from e2e_private_transfer.replay import replay_and_verify  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--seed", type=int, default=123)
    args = parser.parse_args()

    trace, summary = run_private_transfer(seed=args.seed)
    output_path = Path(args.out)
    output_path.write_text(trace.to_json(), encoding="utf-8")
    replay_ok = replay_and_verify(trace)

    print(
        "fee_total="
        f"{summary.fee_total} "
        "tx_hash="
        f"{summary.tx_hash_prefix} "
        "block_hash="
        f"{summary.block_hash_prefix} "
        "state_root="
        f"{summary.state_root_prefix} "
        "receipt_hash="
        f"{summary.receipt_hash_prefix} "
        "replay_ok="
        f"{replay_ok}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
