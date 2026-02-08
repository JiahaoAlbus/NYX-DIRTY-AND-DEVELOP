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


class ServerMetaEndpointsTests(unittest.TestCase):
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

    def _get_json(self, path: str) -> dict:
        conn = HTTPConnection("127.0.0.1", self.port, timeout=10)
        conn.request("GET", path)
        response = conn.getresponse()
        data = response.read()
        self.assertEqual(response.status, 200)
        conn.close()
        return json.loads(data.decode("utf-8"))

    def test_healthz(self) -> None:
        payload = self._get_json("/healthz")
        self.assertTrue(payload.get("ok"))

    def test_version(self) -> None:
        payload = self._get_json("/version")
        self.assertIn("commit", payload)
        self.assertIn("describe", payload)
        self.assertEqual(payload.get("build"), "testnet")

    def test_capabilities(self) -> None:
        payload = self._get_json("/capabilities")
        modules = payload.get("modules")
        self.assertIsInstance(modules, list)
        self.assertIn("exchange", modules)
        endpoints = payload.get("endpoints")
        self.assertIsInstance(endpoints, list)
        self.assertTrue(any("/run" in item for item in endpoints))


if __name__ == "__main__":
    unittest.main()
