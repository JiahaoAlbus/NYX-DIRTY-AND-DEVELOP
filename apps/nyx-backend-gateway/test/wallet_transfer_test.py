import os
import tempfile
import unittest
from pathlib import Path

import _bootstrap  # noqa: F401
from nyx_backend_gateway.gateway import GatewayError, execute_wallet_transfer
from nyx_backend_gateway.storage import apply_wallet_faucet, create_connection


class WalletTransferTests(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["NYX_TESTNET_FEE_ADDRESS"] = "treasury-test"

    def test_transfer_updates_balances_and_fees(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "gateway.db"
            conn = create_connection(db_path)
            apply_wallet_faucet(conn, "sender-001", 1000)
            conn.close()

            result, balances, fee_record = execute_wallet_transfer(
                seed=42,
                run_id="wallet-run-1",
                payload={
                    "from_address": "sender-001",
                    "to_address": "receiver-001",
                    "amount": 10,
                },
                db_path=db_path,
                run_root=Path(tmp) / "runs",
            )

            self.assertEqual(result.run_id, "wallet-run-1")
            self.assertGreater(fee_record.protocol_fee_total, 0)
            self.assertEqual(balances["to_balance"], 10)
            self.assertEqual(
                balances["from_balance"],
                1000 - 10 - fee_record.total_paid,
            )
            self.assertEqual(balances["treasury_balance"], fee_record.total_paid)

    def test_insufficient_balance_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "gateway.db"
            conn = create_connection(db_path)
            apply_wallet_faucet(conn, "sender-002", 2)
            conn.close()

            with self.assertRaises(GatewayError):
                execute_wallet_transfer(
                    seed=7,
                    run_id="wallet-run-2",
                    payload={
                        "from_address": "sender-002",
                        "to_address": "receiver-002",
                        "amount": 10,
                    },
                    db_path=db_path,
                    run_root=Path(tmp) / "runs",
                )


if __name__ == "__main__":
    unittest.main()
