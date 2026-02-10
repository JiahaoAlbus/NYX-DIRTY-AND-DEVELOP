import hashlib
import os
import tempfile
import unittest
from pathlib import Path

import _bootstrap  # noqa: F401
from nyx_backend_gateway.gateway import GatewayError, execute_run
from nyx_backend_gateway.identifiers import wallet_address
from nyx_backend_gateway.storage import apply_wallet_faucet, create_connection, load_by_id


def _receipt_id(run_id: str) -> str:
    digest = hashlib.sha256(f"receipt:{run_id}".encode("utf-8")).hexdigest()
    return f"receipt-{digest[:16]}"


def _find_run_dir(run_root: Path, run_id: str) -> Path | None:
    for entry in run_root.iterdir():
        if not entry.is_dir():
            continue
        run_id_path = entry / "run_id.txt"
        if run_id_path.exists() and run_id_path.read_text(encoding="utf-8").strip() == run_id:
            return entry
    return None


class GatewayFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        os.environ.setdefault("NYX_TESTNET_FEE_ADDRESS", "testnet-fee-address")

    def _run_and_check(self, module: str, action: str, payload: dict) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "gateway.db"
            run_root = Path(tmp) / "runs"
            run_id = f"run-{module}"
            result = execute_run(
                seed=123,
                run_id=run_id,
                module=module,
                action=action,
                payload=payload,
                db_path=db_path,
                run_root=run_root,
            )
            self.assertTrue(result.replay_ok)
            conn = create_connection(db_path)
            evidence = load_by_id(conn, "evidence_runs", "run_id", run_id)
            receipt = load_by_id(conn, "receipts", "receipt_id", _receipt_id(run_id))
            self.assertIsNotNone(evidence)
            self.assertIsNotNone(receipt)
            if module == "exchange":
                fee = load_by_id(conn, "fee_ledger", "run_id", run_id)
                self.assertIsNotNone(fee)
            conn.close()
            run_dir = _find_run_dir(run_root, run_id)
            self.assertIsNotNone(run_dir)
            if run_dir is not None:
                self.assertTrue((run_dir / "evidence.json").exists())

    def test_exchange_flow(self) -> None:
        self._run_and_check(
            "exchange",
            "route_swap",
            {"asset_in": "asset-a", "asset_out": "asset-b", "amount": 5, "min_out": 3},
        )

    def test_exchange_place_order_flow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "gateway.db"
            run_root = Path(tmp) / "runs"
            account_id = "trader-1"
            wallet_addr = wallet_address(account_id)
            conn = create_connection(db_path)
            apply_wallet_faucet(conn, wallet_addr, 1_000, asset_id="NYXT")
            conn.close()

            run_id = "run-exchange-place-order"
            result = execute_run(
                seed=123,
                run_id=run_id,
                module="exchange",
                action="place_order",
                payload={
                    "owner_address": wallet_addr,
                    "side": "BUY",
                    "asset_in": "NYXT",
                    "asset_out": "ECHO",
                    "amount": 100,
                    "price": 10,
                },
                caller_wallet_address=wallet_addr,
                caller_account_id=account_id,
                db_path=db_path,
                run_root=run_root,
            )
            self.assertTrue(result.replay_ok)
            conn = create_connection(db_path)
            evidence = load_by_id(conn, "evidence_runs", "run_id", run_id)
            receipt = load_by_id(conn, "receipts", "receipt_id", _receipt_id(run_id))
            fee = load_by_id(conn, "fee_ledger", "run_id", run_id)
            self.assertIsNotNone(evidence)
            self.assertIsNotNone(receipt)
            self.assertIsNotNone(fee)
            conn.close()

    def test_exchange_cancel_order_flow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "gateway.db"
            run_root = Path(tmp) / "runs"
            account_id = "trader-2"
            wallet_addr = wallet_address(account_id)
            conn = create_connection(db_path)
            apply_wallet_faucet(conn, wallet_addr, 1_000, asset_id="NYXT")
            conn.close()

            run_id_order = "run-exchange-cancel-order-place"
            execute_run(
                seed=123,
                run_id=run_id_order,
                module="exchange",
                action="place_order",
                payload={
                    "owner_address": wallet_addr,
                    "side": "BUY",
                    "asset_in": "NYXT",
                    "asset_out": "ECHO",
                    "amount": 50,
                    "price": 10,
                },
                caller_wallet_address=wallet_addr,
                caller_account_id=account_id,
                db_path=db_path,
                run_root=run_root,
            )

            order_id = f"order-{hashlib.sha256(f'order:{run_id_order}'.encode('utf-8')).hexdigest()[:16]}"
            run_id_cancel = "run-exchange-cancel-order"
            result = execute_run(
                seed=123,
                run_id=run_id_cancel,
                module="exchange",
                action="cancel_order",
                payload={"order_id": order_id},
                caller_wallet_address=wallet_addr,
                caller_account_id=account_id,
                db_path=db_path,
                run_root=run_root,
            )
            self.assertTrue(result.replay_ok)

    def test_chat_flow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "gateway.db"
            run_root = Path(tmp) / "runs"
            conn = create_connection(db_path)
            wallet_addr = wallet_address("acct-1")
            apply_wallet_faucet(conn, wallet_addr, 1_000, asset_id="NYXT")
            conn.close()
            run_id = "run-chat"
            result = execute_run(
                seed=123,
                run_id=run_id,
                module="chat",
                action="message_event",
                payload={"channel": "dm/acct-1/acct-2", "message": '{"ciphertext":"AA==","iv":"BB=="}'},
                caller_wallet_address=wallet_addr,
                caller_account_id="acct-1",
                db_path=db_path,
                run_root=run_root,
            )
            self.assertTrue(result.replay_ok)

    def test_marketplace_flow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "gateway.db"
            run_root = Path(tmp) / "runs"
            with self.assertRaises(GatewayError):
                execute_run(
                    seed=123,
                    run_id="run-market-unsupported",
                    module="marketplace",
                    action="order_intent",
                    payload={"sku": "sku-1", "title": "Item One", "price": 10, "qty": 2},
                    caller_account_id="buyer-1",
                    db_path=db_path,
                    run_root=run_root,
                )

    def test_marketplace_listing_flow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "gateway.db"
            run_root = Path(tmp) / "runs"
            account_id = "seller-1"
            wallet_addr = wallet_address(account_id)
            conn = create_connection(db_path)
            apply_wallet_faucet(conn, wallet_addr, 1_000, asset_id="NYXT")
            conn.close()

            run_id = "run-market-listing"
            result = execute_run(
                seed=123,
                run_id=run_id,
                module="marketplace",
                action="listing_publish",
                payload={"publisher_id": wallet_addr, "sku": "sku-2", "title": "Item Two", "price": 12},
                caller_wallet_address=wallet_addr,
                caller_account_id=account_id,
                db_path=db_path,
                run_root=run_root,
            )
            self.assertTrue(result.replay_ok)

    def test_marketplace_purchase_flow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "gateway.db"
            run_root = Path(tmp) / "runs"
            seller_id = "seller-9"
            buyer_id = "buyer-9"
            seller_wallet = wallet_address(seller_id)
            buyer_wallet = wallet_address(buyer_id)
            conn = create_connection(db_path)
            apply_wallet_faucet(conn, seller_wallet, 1_000, asset_id="NYXT")
            apply_wallet_faucet(conn, buyer_wallet, 10_000, asset_id="NYXT")
            conn.close()

            run_id_listing = "run-listing"
            execute_run(
                seed=123,
                run_id=run_id_listing,
                module="marketplace",
                action="listing_publish",
                payload={"publisher_id": seller_wallet, "sku": "sku-9", "title": "Item Nine", "price": 9},
                caller_wallet_address=seller_wallet,
                caller_account_id=seller_id,
                db_path=db_path,
                run_root=run_root,
            )
            listing_id = f"listing-{hashlib.sha256(f'listing:{run_id_listing}'.encode('utf-8')).hexdigest()[:16]}"
            result = execute_run(
                seed=123,
                run_id="run-purchase",
                module="marketplace",
                action="purchase_listing",
                payload={"buyer_id": buyer_wallet, "listing_id": listing_id, "qty": 1},
                caller_wallet_address=buyer_wallet,
                caller_account_id=buyer_id,
                db_path=db_path,
                run_root=run_root,
            )
            self.assertTrue(result.replay_ok)

    def test_entertainment_flow(self) -> None:
        self._run_and_check(
            "entertainment",
            "state_step",
            {"item_id": "ent-001", "mode": "pulse", "step": 2},
        )


if __name__ == "__main__":
    unittest.main()
