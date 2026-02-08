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


class ServerEntertainmentSmokeTests(unittest.TestCase):
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

    def test_entertainment_step_flow(self) -> None:
        conn = HTTPConnection("127.0.0.1", self.port, timeout=10)
        conn.request("GET", "/entertainment/items")
        response = conn.getresponse()
        data = response.read()
        self.assertEqual(response.status, 200)
        items = json.loads(data.decode("utf-8")).get("items") or []
        self.assertTrue(items)
        item_id = items[0]["item_id"]
        conn.close()

        conn = HTTPConnection("127.0.0.1", self.port, timeout=10)
        payload = {
            "seed": 321,
            "run_id": "run-ent-1",
            "payload": {"item_id": item_id, "mode": "pulse", "step": 1},
        }
        body = json.dumps(payload, separators=(",", ":"))
        conn.request("POST", "/entertainment/step", body=body, headers={"Content-Type": "application/json"})
        response = conn.getresponse()
        data = response.read()
        self.assertEqual(response.status, 200)
        parsed = json.loads(data.decode("utf-8"))
        self.assertEqual(parsed.get("status"), "complete")
        conn.close()

        conn = HTTPConnection("127.0.0.1", self.port, timeout=10)
        conn.request("GET", "/entertainment/events?item_id=" + item_id)
        response = conn.getresponse()
        data = response.read()
        self.assertEqual(response.status, 200)
        parsed = json.loads(data.decode("utf-8"))
        self.assertIn("events", parsed)
        conn.close()


if __name__ == "__main__":
    unittest.main()
