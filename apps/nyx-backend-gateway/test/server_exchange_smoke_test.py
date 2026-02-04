import _bootstrap
import base64
import hmac
import json
import os
import tempfile
import threading
from http.client import HTTPConnection
from pathlib import Path
import unittest

import nyx_backend_gateway.gateway as gateway
import nyx_backend_gateway.server as server


class ServerExchangeSmokeTests(unittest.TestCase):
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

    def _auth_token(self) -> tuple[str, str]:
        key = b"portal-key-0006-0006-0006-0006"
        pubkey = base64.b64encode(key).decode("utf-8")
        status, created = self._post("/portal/v1/accounts", {"handle": "trader", "pubkey": pubkey})
        self.assertEqual(status, 200)
        account_id = created.get("account_id")
        status, challenge = self._post("/portal/v1/auth/challenge", {"account_id": account_id})
        self.assertEqual(status, 200)
        nonce = challenge.get("nonce")
        signature = base64.b64encode(hmac.new(key, nonce.encode("utf-8"), "sha256").digest()).decode(
            "utf-8"
        )
        status, verified = self._post(
            "/portal/v1/auth/verify",
            {"account_id": account_id, "nonce": nonce, "signature": signature},
        )
        self.assertEqual(status, 200)
        return account_id, verified.get("access_token")

    def test_exchange_place_order_and_orderbook(self) -> None:
        account_id, token = self._auth_token()
        status, _ = self._post(
            "/wallet/v1/faucet",
            {"seed": 123, "run_id": "run-exchange-faucet", "address": account_id, "amount": 1000, "asset_id": "NYXT"},
            token=token,
        )
        self.assertEqual(status, 200)

        status, parsed = self._post(
            "/exchange/place_order",
            {
                "seed": 123,
                "run_id": "run-exchange-1",
                "payload": {
                    "owner_address": account_id,
                    "side": "BUY",
                    "asset_in": "NYXT",
                    "asset_out": "ECHO",
                    "amount": 100,
                    "price": 10,
                },
            },
            token=token,
        )
        self.assertEqual(status, 200)
        self.assertEqual(parsed.get("status"), "complete")
        self.assertIn("state_hash", parsed)
        self.assertIn("receipt_hashes", parsed)
        self.assertIn("fee_total", parsed)

        conn = HTTPConnection("127.0.0.1", self.port, timeout=10)
        conn.request("GET", "/exchange/orderbook")
        response = conn.getresponse()
        data = response.read()
        self.assertEqual(response.status, 200)
        parsed = json.loads(data.decode("utf-8"))
        self.assertIn("buy", parsed)
        self.assertIn("sell", parsed)
        conn.close()


if __name__ == "__main__":
    unittest.main()
