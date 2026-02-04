import _bootstrap
import tempfile
from pathlib import Path
import unittest

from nyx_backend_gateway.exchange import place_order
from nyx_backend_gateway.storage import Order, apply_wallet_faucet, create_connection, list_orders, list_trades


class ExchangeEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        db_path = Path(self.tmp.name) / "gateway.db"
        self.conn = create_connection(db_path)

    def tearDown(self) -> None:
        self.conn.close()
        self.tmp.cleanup()

    def test_full_match_removes_orders(self) -> None:
        apply_wallet_faucet(self.conn, "seller-1", 1000, asset_id="ECHO")
        apply_wallet_faucet(self.conn, "buyer-1", 1000, asset_id="NYXT")
        sell = Order(
            order_id="sell-1",
            owner_address="seller-1",
            side="SELL",
            amount=5,
            price=10,
            asset_in="ECHO",
            asset_out="NYXT",
            run_id="run-sell",
        )
        place_order(self.conn, sell)
        buy = Order(
            order_id="buy-1",
            owner_address="buyer-1",
            side="BUY",
            amount=50,
            price=12,
            asset_in="NYXT",
            asset_out="ECHO",
            run_id="run-buy",
        )
        result = place_order(self.conn, buy)
        self.assertEqual(len(result.trades), 1)
        orders = list_orders(self.conn)
        self.assertEqual(len(orders), 0)
        trades = list_trades(self.conn)
        self.assertEqual(len(trades), 2)

    def test_partial_match_keeps_remainder(self) -> None:
        apply_wallet_faucet(self.conn, "seller-2", 1000, asset_id="ECHO")
        apply_wallet_faucet(self.conn, "buyer-2", 1000, asset_id="NYXT")
        sell = Order(
            order_id="sell-2",
            owner_address="seller-2",
            side="SELL",
            amount=10,
            price=9,
            asset_in="ECHO",
            asset_out="NYXT",
            run_id="run-sell-2",
        )
        place_order(self.conn, sell)
        buy = Order(
            order_id="buy-2",
            owner_address="buyer-2",
            side="BUY",
            amount=36,
            price=9,
            asset_in="NYXT",
            asset_out="ECHO",
            run_id="run-buy-2",
        )
        place_order(self.conn, buy)
        orders = list_orders(self.conn, side="SELL")
        self.assertEqual(len(orders), 1)
        self.assertEqual(int(orders[0]["amount"]), 6)


if __name__ == "__main__":
    unittest.main()
