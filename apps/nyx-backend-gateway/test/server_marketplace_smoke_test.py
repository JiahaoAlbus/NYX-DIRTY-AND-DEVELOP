import base64
import hmac
import json
import os
import tempfile
import threading
import unittest
from http.client import HTTPConnection
from pathlib import Path

import _bootstrap  # noqa: F401
import nyx_backend_gateway.gateway as gateway
import nyx_backend_gateway.server as server


class ServerMarketplaceSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        os.environ.setdefault("NYX_TESTNET_FEE_ADDRESS", "testnet-fee-address")
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "gateway.db"
        self.run_root = Path(self.tmp.name) / "runs"
        gateway._db_path = lambda: self.db_path
        gateway._run_root = lambda: self.run_root
        server._db_path = lambda: self.db_path
        server._run_root = lambda: self.run_root
        self.httpd = server.ThreadingHTTPServer(("127.0.0.1", 0), server.GatewayHandler)
        self.httpd.rate_limiter = server.RequestLimiter(100, 60)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.port = self.httpd.server_address[1]

    def tearDown(self) -> None:
        self.httpd.shutdown()
        self.thread.join(timeout=2)
        self.httpd.server_close()
        self.tmp.cleanup()

    def _post(self, path: str, payload: dict, token: str | None = None) -> tuple[int, dict]:
        conn = HTTPConnection("127.0.0.1", self.port, timeout=10)
        body = json.dumps(payload, separators=(",", ":"))
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        conn.request("POST", path, body=body, headers=headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()
        return response.status, json.loads(data.decode("utf-8"))

    def _auth_token(self, handle: str) -> tuple[str, str, str]:
        key = f"portal-key-{handle}-0001".encode("utf-8")
        pubkey = base64.b64encode(key).decode("utf-8")
        status, created = self._post("/portal/v1/accounts", {"handle": handle, "pubkey": pubkey})
        self.assertEqual(status, 200)
        account_id = created.get("account_id")
        wallet_address = created.get("wallet_address")
        status, challenge = self._post("/portal/v1/auth/challenge", {"account_id": account_id})
        self.assertEqual(status, 200)
        nonce = challenge.get("nonce")
        signature = base64.b64encode(hmac.new(key, nonce.encode("utf-8"), "sha256").digest()).decode("utf-8")
        status, verified = self._post(
            "/portal/v1/auth/verify",
            {"account_id": account_id, "nonce": nonce, "signature": signature},
        )
        self.assertEqual(status, 200)
        return account_id, wallet_address, verified.get("access_token")

    def test_listing_and_purchase(self) -> None:
        _, seller_wallet, seller_token = self._auth_token("seller")
        _, buyer_wallet, buyer_token = self._auth_token("buyer")

        status, _ = self._post(
            "/wallet/v1/faucet",
            {
                "seed": 123,
                "run_id": "run-market-faucet-seller",
                "address": seller_wallet,
                "amount": 1000,
                "asset_id": "NYXT",
            },
            token=seller_token,
        )
        self.assertEqual(status, 200)
        status, _ = self._post(
            "/wallet/v1/faucet",
            {
                "seed": 123,
                "run_id": "run-market-faucet-buyer",
                "address": buyer_wallet,
                "amount": 1000,
                "asset_id": "NYXT",
            },
            token=buyer_token,
        )
        self.assertEqual(status, 200)

        status, parsed = self._post(
            "/marketplace/listing",
            {"seed": 123, "run_id": "run-listing-1", "payload": {"sku": "sku-1", "title": "Item One", "price": 10}},
            token=seller_token,
        )
        self.assertEqual(status, 200)
        self.assertEqual(parsed.get("status"), "complete")

        conn = HTTPConnection("127.0.0.1", self.port, timeout=10)
        conn.request("GET", "/marketplace/listings")
        response = conn.getresponse()
        data = response.read()
        self.assertEqual(response.status, 200)
        parsed = json.loads(data.decode("utf-8"))
        self.assertIn("listings", parsed)
        listings = parsed.get("listings") or []
        listing_id = listings[0]["listing_id"]
        conn.close()

        status, parsed = self._post(
            "/marketplace/purchase",
            {"seed": 123, "run_id": "run-purchase-1", "payload": {"listing_id": listing_id, "qty": 1}},
            token=buyer_token,
        )
        self.assertEqual(status, 200)
        self.assertEqual(parsed.get("status"), "complete")

        conn = HTTPConnection("127.0.0.1", self.port, timeout=10)
        conn.request("GET", "/marketplace/purchases?listing_id=" + listing_id)
        response = conn.getresponse()
        data = response.read()
        self.assertEqual(response.status, 200)
        parsed = json.loads(data.decode("utf-8"))
        self.assertIn("purchases", parsed)
        conn.close()

        conn = HTTPConnection("127.0.0.1", self.port, timeout=10)
        conn.request(
            "GET", "/marketplace/v1/my_purchases?limit=10&offset=0", headers={"Authorization": f"Bearer {buyer_token}"}
        )
        response = conn.getresponse()
        data = response.read()
        self.assertEqual(response.status, 200)
        parsed = json.loads(data.decode("utf-8"))
        self.assertGreaterEqual(len(parsed.get("purchases") or []), 1)
        conn.close()


if __name__ == "__main__":
    unittest.main()
