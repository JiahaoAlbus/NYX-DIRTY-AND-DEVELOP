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


class ServerWalletSmokeTests(unittest.TestCase):
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

    def test_wallet_faucet_and_transfer(self) -> None:
        conn = HTTPConnection("127.0.0.1", self.port, timeout=10)
        faucet_payload = {
            "seed": 123,
            "run_id": "wallet-faucet-1",
            "payload": {"address": "wallet-a", "amount": 1000},
        }
        conn.request("POST", "/wallet/faucet", body=json.dumps(faucet_payload), headers={"Content-Type": "application/json"})
        response = conn.getresponse()
        data = response.read()
        self.assertEqual(response.status, 200)
        parsed = json.loads(data.decode("utf-8"))
        self.assertEqual(parsed.get("status"), "complete")
        conn.close()

        conn = HTTPConnection("127.0.0.1", self.port, timeout=10)
        transfer_payload = {
            "seed": 123,
            "run_id": "wallet-transfer-1",
            "payload": {"from_address": "wallet-a", "to_address": "wallet-b", "amount": 10},
        }
        conn.request("POST", "/wallet/transfer", body=json.dumps(transfer_payload), headers={"Content-Type": "application/json"})
        response = conn.getresponse()
        data = response.read()
        self.assertEqual(response.status, 200)
        parsed = json.loads(data.decode("utf-8"))
        self.assertEqual(parsed.get("status"), "complete")
        self.assertIn("fee_total", parsed)
        conn.close()

        conn = HTTPConnection("127.0.0.1", self.port, timeout=10)
        conn.request("GET", "/wallet/balance?address=wallet-a")
        response = conn.getresponse()
        data = response.read()
        self.assertEqual(response.status, 200)
        parsed = json.loads(data.decode("utf-8"))
        self.assertIn("balance", parsed)
        conn.close()


if __name__ == "__main__":
    unittest.main()
