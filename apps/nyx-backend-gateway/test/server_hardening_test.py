import json
import os
import tempfile
import threading
from http.client import HTTPConnection
from pathlib import Path
import unittest

import nyx_backend_gateway.gateway as gateway
import nyx_backend_gateway.server as server


class ServerHardeningTests(unittest.TestCase):
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

    def test_invalid_run_id_rejected(self) -> None:
        conn = HTTPConnection("127.0.0.1", self.port, timeout=10)
        payload = {
            "seed": 123,
            "run_id": "../bad",
            "module": "exchange",
            "action": "route_swap",
            "payload": {"asset_in": "asset-a", "asset_out": "asset-b", "amount": 5, "min_out": 3},
        }
        body = json.dumps(payload, separators=(",", ":"))
        conn.request("POST", "/run", body=body, headers={"Content-Type": "application/json"})
        response = conn.getresponse()
        response.read()
        self.assertEqual(response.status, 400)
        conn.close()

    def test_message_too_long_rejected(self) -> None:
        conn = HTTPConnection("127.0.0.1", self.port, timeout=10)
        payload = {
            "seed": 123,
            "run_id": "run-chat-long",
            "payload": {"channel": "general", "message": "x" * 600},
        }
        body = json.dumps(payload, separators=(",", ":"))
        conn.request("POST", "/chat/send", body=body, headers={"Content-Type": "application/json"})
        response = conn.getresponse()
        response.read()
        self.assertEqual(response.status, 400)
        conn.close()

    def test_payload_too_large_rejected(self) -> None:
        conn = HTTPConnection("127.0.0.1", self.port, timeout=10)
        payload = {
            "seed": 1,
            "run_id": "run-large",
            "module": "exchange",
            "action": "route_swap",
            "payload": {"text": "y" * 6000},
        }
        body = json.dumps(payload, separators=(",", ":"))
        conn.request("POST", "/run", body=body, headers={"Content-Type": "application/json"})
        response = conn.getresponse()
        response.read()
        self.assertEqual(response.status, 400)
        conn.close()


if __name__ == "__main__":
    unittest.main()
