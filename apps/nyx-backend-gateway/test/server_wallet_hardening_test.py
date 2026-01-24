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


class ServerWalletHardeningTests(unittest.TestCase):
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

    def _post_json(self, path: str, payload: dict) -> tuple[int, dict]:
        conn = HTTPConnection("127.0.0.1", self.port, timeout=10)
        body = json.dumps(payload, separators=(",", ":"))
        conn.request("POST", path, body=body, headers={"Content-Type": "application/json"})
        response = conn.getresponse()
        data = response.read()
        conn.close()
        return response.status, json.loads(data.decode("utf-8"))

    def test_rejects_negative_amount(self) -> None:
        payload = {
            "seed": 1,
            "run_id": "run-wallet-bad-amount",
            "payload": {
                "from_address": "addr-a",
                "to_address": "addr-b",
                "amount": -1,
            },
        }
        status, _ = self._post_json("/wallet/transfer", payload)
        self.assertEqual(status, 400)

    def test_rejects_invalid_address(self) -> None:
        payload = {
            "seed": 1,
            "run_id": "run-wallet-bad-address",
            "payload": {
                "from_address": "bad addr",
                "to_address": "addr-b",
                "amount": 1,
            },
        }
        status, _ = self._post_json("/wallet/transfer", payload)
        self.assertEqual(status, 400)


if __name__ == "__main__":
    unittest.main()
