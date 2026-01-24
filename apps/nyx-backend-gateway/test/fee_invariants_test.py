import _bootstrap
import os
import unittest

from nyx_backend_gateway.fees import route_fee


class FeeInvariantTests(unittest.TestCase):
    def setUp(self) -> None:
        os.environ.setdefault("NYX_TESTNET_FEE_ADDRESS", "testnet-fee-address")

    def test_protocol_fee_nonzero_and_additive(self) -> None:
        payload = {
            "side": "BUY",
            "asset_in": "asset-a",
            "asset_out": "asset-b",
            "amount": 5,
            "price": 10,
        }
        ledger = route_fee("exchange", "place_order", payload, "run-fee-1")
        self.assertGreater(ledger.protocol_fee_total, 0)
        self.assertGreaterEqual(ledger.platform_fee_amount, 0)
        self.assertEqual(
            ledger.total_paid,
            ledger.protocol_fee_total + ledger.platform_fee_amount,
        )


if __name__ == "__main__":
    unittest.main()
