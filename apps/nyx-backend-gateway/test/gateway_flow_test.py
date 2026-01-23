import hashlib
import os
import tempfile
from pathlib import Path
import unittest

from nyx_backend_gateway.gateway import execute_run
from nyx_backend_gateway.storage import create_connection, load_by_id


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
        self._run_and_check(
            "exchange",
            "place_order",
            {
                "side": "BUY",
                "asset_in": "asset-a",
                "asset_out": "asset-b",
                "amount": 5,
                "price": 10,
            },
        )

    def test_exchange_cancel_order_flow(self) -> None:
        self._run_and_check(
            "exchange",
            "cancel_order",
            {"order_id": "order-unknown"},
        )

    def test_chat_flow(self) -> None:
        self._run_and_check(
            "chat",
            "message_event",
            {"channel": "general", "message": "hello"},
        )

    def test_marketplace_flow(self) -> None:
        self._run_and_check(
            "marketplace",
            "order_intent",
            {"sku": "sku-1", "title": "Item One", "price": 10, "qty": 2},
        )

    def test_marketplace_listing_flow(self) -> None:
        self._run_and_check(
            "marketplace",
            "listing_publish",
            {"sku": "sku-2", "title": "Item Two", "price": 12},
        )

    def test_marketplace_purchase_flow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "gateway.db"
            run_root = Path(tmp) / "runs"
            run_id_listing = "run-listing"
            execute_run(
                seed=123,
                run_id=run_id_listing,
                module="marketplace",
                action="listing_publish",
                payload={"sku": "sku-9", "title": "Item Nine", "price": 9},
                db_path=db_path,
                run_root=run_root,
            )
            listing_id = f"listing-{hashlib.sha256(f'listing:{run_id_listing}'.encode('utf-8')).hexdigest()[:16]}"
            result = execute_run(
                seed=123,
                run_id="run-purchase",
                module="marketplace",
                action="purchase_listing",
                payload={"listing_id": listing_id, "qty": 1},
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
