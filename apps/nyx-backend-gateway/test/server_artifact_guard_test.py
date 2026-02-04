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


class ServerArtifactGuardTests(unittest.TestCase):
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

    def _post(self, path: str, payload: dict, token: str | None = None) -> dict:
        conn = HTTPConnection("127.0.0.1", self.port, timeout=10)
        body = json.dumps(payload, separators=(",", ":"))
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        conn.request("POST", path, body=body, headers=headers)
        response = conn.getresponse()
        data = response.read()
        self.assertEqual(response.status, 200)
        conn.close()
        return json.loads(data.decode("utf-8"))

    def _auth_token(self) -> tuple[str, str]:
        key = b"portal-key-art-0001"
        pubkey = base64.b64encode(key).decode("utf-8")
        created = self._post("/portal/v1/accounts", {"handle": "archivist", "pubkey": pubkey})
        account_id = created.get("account_id")
        challenge = self._post("/portal/v1/auth/challenge", {"account_id": account_id})
        nonce = challenge.get("nonce")
        signature = base64.b64encode(hmac.new(key, nonce.encode("utf-8"), "sha256").digest()).decode("utf-8")
        verified = self._post("/portal/v1/auth/verify", {"account_id": account_id, "nonce": nonce, "signature": signature})
        return account_id, verified.get("access_token")

    def test_artifact_path_traversal_rejected(self) -> None:
        _, token = self._auth_token()
        self._post(
            "/run",
            {
                "seed": 123,
                "run_id": "artifact-run-1",
                "module": "exchange",
                "action": "route_swap",
                "payload": {"asset_in": "asset-a", "asset_out": "asset-b", "amount": 5, "min_out": 3},
            },
            token=token,
        )
        conn = HTTPConnection("127.0.0.1", self.port, timeout=10)
        conn.request("GET", "/artifact?run_id=artifact-run-1&name=../x")
        response = conn.getresponse()
        response.read()
        self.assertEqual(response.status, 400)
        conn.close()


if __name__ == "__main__":
    unittest.main()
