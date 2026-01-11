from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _add_paths() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    paths = [
        repo_root / "packages" / "e2e-demo" / "src",
        repo_root / "packages" / "l0-zk-id" / "src",
        repo_root / "packages" / "l2-economics" / "src",
        repo_root / "packages" / "l1-chain" / "src",
        repo_root / "packages" / "wallet-kernel" / "src",
    ]
    for path in paths:
        path_str = str(path)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)


_add_paths()

from e2e_demo.pipeline import run_e2e  # noqa: E402
from e2e_demo.replay import replay_and_verify  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="NYX Week7 E2E demo")
    parser.add_argument("--out", type=str, required=True, help="Output trace json path")
    parser.add_argument("--seed", type=int, default=123, help="Deterministic seed")
    args = parser.parse_args()

    trace, summary = run_e2e(seed=args.seed)
    result = replay_and_verify(trace)

    Path(args.out).write_text(trace.to_json(), encoding="utf-8")

    line = (
        "summary: "
        f"identity_commitment={summary.identity_commitment_prefix} "
        f"fee_total={summary.fee_total} "
        f"tx_hash={summary.tx_hash_prefix} "
        f"block_hash={summary.block_hash_prefix} "
        f"state_root={summary.state_root_prefix} "
        f"receipt_hash={summary.receipt_hash_prefix} "
        f"replay_ok={result.ok}"
    )
    print(line)


if __name__ == "__main__":
    main()
