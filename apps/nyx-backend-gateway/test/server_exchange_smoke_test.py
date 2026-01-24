import _bootstrap
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

    def test_exchange_place_order_and_orderbook(self) -> None:
        conn = HTTPConnection("127.0.0.1", self.port, timeout=10)
        payload = {
            "seed": 123,
            "run_id": "run-exchange-1",
            "payload": {
                "side": "BUY",
                "asset_in": "asset-a",
                "asset_out": "asset-b",
                "amount": 5,
                "price": 10,
            },
        }
        body = json.dumps(payload, separators=(",", ":"))
        conn.request("POST", "/exchange/place_order", body=body, headers={"Content-Type": "application/json"})
        response = conn.getresponse()
        data = response.read()
        self.assertEqual(response.status, 200)
        parsed = json.loads(data.decode("utf-8"))
        self.assertEqual(parsed.get("status"), "complete")
        conn.close()

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
