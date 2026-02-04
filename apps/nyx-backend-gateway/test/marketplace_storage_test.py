import _bootstrap
import tempfile
from pathlib import Path
import unittest

from nyx_backend_gateway.storage import Listing, Purchase, create_connection, insert_listing, insert_purchase, list_listings, list_purchases


class MarketplaceStorageTests(unittest.TestCase):
    def test_listings_and_purchases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            conn = create_connection(Path(tmp) / "gateway.db")
            insert_listing(
                conn,
                Listing(
                    listing_id="list-1",
                    publisher_id="seller-1",
                    sku="sku-1",
                    title="Item One",
                    price=10,
                    status="active",
                    run_id="run-1",
                ),
            )
            insert_purchase(
                conn,
                Purchase(purchase_id="purchase-1", listing_id="list-1", buyer_id="buyer-1", qty=2, run_id="run-2"),
            )
            listings = list_listings(conn)
            purchases = list_purchases(conn, listing_id="list-1")
            self.assertEqual(len(listings), 1)
            self.assertEqual(len(purchases), 1)
            conn.close()


if __name__ == "__main__":
    unittest.main()
