#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _ensure_paths() -> None:
    repo_root = _repo_root()
    paths = [
        repo_root / "apps" / "nyx-backend-gateway" / "src",
        repo_root / "apps" / "nyx-backend" / "src",
    ]
    for path in paths:
        path_str = str(path)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)


def main() -> int:
    parser = argparse.ArgumentParser(description="Q10 one-shot repro (testnet beta)")
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--run-id", default="q10-repro-1")
    args = parser.parse_args()

    _ensure_paths()
    from nyx_backend_gateway.gateway import execute_run, execute_wallet_faucet, execute_wallet_transfer

    os.environ.setdefault("NYX_TESTNET_FEE_ADDRESS", "testnet-fee-address")

    with tempfile.TemporaryDirectory() as tmp:
        run_root = Path(tmp) / "runs"
        db_path = Path(tmp) / "gateway.db"

        wallet_address = "wallet-alpha"
        _, faucet_balance = execute_wallet_faucet(
            seed=args.seed,
            run_id=f"{args.run_id}-faucet",
            payload={"address": wallet_address, "amount": 1000},
            run_root=run_root,
            db_path=db_path,
        )

        transfer_result, balances, fee_record = execute_wallet_transfer(
            seed=args.seed,
            run_id=f"{args.run_id}-transfer",
            payload={
                "from_address": wallet_address,
                "to_address": "wallet-beta",
                "amount": 10,
            },
            run_root=run_root,
            db_path=db_path,
        )

        exchange_result = execute_run(
            seed=args.seed,
            run_id=f"{args.run_id}-exchange",
            module="exchange",
            action="place_order",
            payload={
                "side": "BUY",
                "asset_in": "asset-a",
                "asset_out": "asset-b",
                "amount": 5,
                "price": 10,
            },
            run_root=run_root,
            db_path=db_path,
        )

        print("seed:", args.seed)
        print("wallet_faucet_balance:", faucet_balance)
        print("wallet_transfer_state_hash:", transfer_result.state_hash)
        print("wallet_transfer_receipts:", transfer_result.receipt_hashes)
        print("wallet_transfer_fee_total:", fee_record.total_paid)
        print("wallet_balances:", balances)
        print("exchange_state_hash:", exchange_result.state_hash)
        print("exchange_receipts:", exchange_result.receipt_hashes)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
