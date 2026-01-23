import _bootstrap
import tempfile
from pathlib import Path
import unittest

from nyx_backend_gateway.storage import (
    EvidenceRun,
    Listing,
    MessageEvent,
    Order,
    Purchase,
    Receipt,
    Trade,
    create_connection,
    insert_evidence_run,
    insert_listing,
    insert_message_event,
    insert_order,
    insert_purchase,
    insert_receipt,
    insert_trade,
    load_by_id,
)


class StorageRoundtripTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        db_path = Path(self.tmp.name) / "gateway.db"
        self.conn = create_connection(db_path)

    def tearDown(self) -> None:
        self.conn.close()
        self.tmp.cleanup()

    def test_insert_and_load_records(self) -> None:
        run = EvidenceRun(
            run_id="run-001",
            module="exchange",
            action="route_swap",
            seed=123,
            state_hash="aabbccdd11223344",
            receipt_hashes=["aa11", "bb22"],
            replay_ok=True,
        )
        insert_evidence_run(self.conn, run)
        record = load_by_id(self.conn, "evidence_runs", "run_id", "run-001")
        self.assertIsNotNone(record)

        order = Order(
            order_id="order-1",
            side="BUY",
            amount=5,
            price=7,
            asset_in="asset-a",
            asset_out="asset-b",
            run_id="run-001",
        )
        insert_order(self.conn, order)
        self.assertIsNotNone(load_by_id(self.conn, "orders", "order_id", "order-1"))

        trade = Trade(
            trade_id="trade-1",
            order_id="order-1",
            amount=5,
            price=7,
            run_id="run-001",
        )
        insert_trade(self.conn, trade)
        self.assertIsNotNone(load_by_id(self.conn, "trades", "trade_id", "trade-1"))

        message = MessageEvent(
            message_id="msg-1",
            channel="general",
            body="hello",
            run_id="run-001",
        )
        insert_message_event(self.conn, message)
        self.assertIsNotNone(load_by_id(self.conn, "messages", "message_id", "msg-1"))

        listing = Listing(
            listing_id="list-1",
            sku="sku-1",
            title="Item One",
            price=10,
            run_id="run-001",
        )
        insert_listing(self.conn, listing)
        self.assertIsNotNone(load_by_id(self.conn, "listings", "listing_id", "list-1"))

        purchase = Purchase(
            purchase_id="purchase-1",
            listing_id="list-1",
            qty=2,
            run_id="run-001",
        )
        insert_purchase(self.conn, purchase)
        self.assertIsNotNone(load_by_id(self.conn, "purchases", "purchase_id", "purchase-1"))

        receipt = Receipt(
            receipt_id="receipt-1",
            module="exchange",
            action="route_swap",
            state_hash="aabbccdd11223344",
            receipt_hashes=["aa11", "bb22"],
            replay_ok=True,
            run_id="run-001",
        )
        insert_receipt(self.conn, receipt)
        self.assertIsNotNone(load_by_id(self.conn, "receipts", "receipt_id", "receipt-1"))


if __name__ == "__main__":
    unittest.main()
