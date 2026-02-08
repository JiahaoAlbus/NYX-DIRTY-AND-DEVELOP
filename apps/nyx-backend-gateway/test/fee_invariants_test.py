import os
import unittest

import _bootstrap  # noqa: F401
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

    def test_marketplace_fee_additive(self) -> None:
        payload = {
            "sku": "sku-1",
            "title": "Item One",
            "price": 10,
        }
        ledger = route_fee("marketplace", "listing_publish", payload, "run-fee-2")
        self.assertGreater(ledger.protocol_fee_total, 0)
        self.assertEqual(
            ledger.total_paid,
            ledger.protocol_fee_total + ledger.platform_fee_amount,
        )

    def test_nonzero_fee_for_state_mutations(self) -> None:
        scenarios = [
            ("wallet", "transfer", {"amount": 10}),
            ("wallet", "faucet", {"amount": 100}),
            ("wallet", "airdrop", {"amount": 100}),
            ("exchange", "place_order", {"amount": 5, "price": 10}),
            ("exchange", "cancel_order", {"amount": 1}),
            ("marketplace", "listing_publish", {"price": 10}),
            ("marketplace", "purchase_listing", {"qty": 1, "price": 10}),
            ("chat", "message_event", {"amount": 1}),
            ("web2", "guard_request", {"amount": 1}),
        ]
        for module, action, payload in scenarios:
            ledger = route_fee(module, action, payload, f"run-{module}-{action}")
            self.assertGreater(
                ledger.total_paid,
                0,
                msg=f"{module}.{action} fee_total should be > 0",
            )


if __name__ == "__main__":
    unittest.main()
