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


class ServerPortalActivityTests(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["NYX_TESTNET_FEE_ADDRESS"] = "testnet-fee-address"
        os.environ.pop("NYX_TESTNET_TREASURY_ADDRESS", None)
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "gateway.db"
        self.run_root = Path(self.tmp.name) / "runs"
        gateway._db_path = lambda: self.db_path
        gateway._run_root = lambda: self.run_root
        server._db_path = lambda: self.db_path
        server._run_root = lambda: self.run_root
        self.httpd = server.ThreadingHTTPServer(("127.0.0.1", 0), server.GatewayHandler)
        self.httpd.rate_limiter = server.RequestLimiter(100, 60)
        self.httpd.account_limiter = server.RequestLimiter(100, 60)
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

    def _get(self, path: str, token: str | None = None) -> tuple[int, dict]:
        conn = HTTPConnection("127.0.0.1", self.port, timeout=10)
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        conn.request("GET", path, headers=headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()
        return response.status, json.loads(data.decode("utf-8"))

    def _auth_token(self) -> tuple[str, str, str]:
        key = b"portal-key-activity-0001"
        pubkey = base64.b64encode(key).decode("utf-8")
        status, created = self._post("/portal/v1/accounts", {"handle": "activity", "pubkey": pubkey})
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

    def test_activity_returns_receipts(self) -> None:
        _, wallet_address, token = self._auth_token()
        status, _ = self._post(
            "/wallet/v1/faucet",
            {
                "seed": 7,
                "run_id": "activity-faucet",
                "address": wallet_address,
                "amount": 1000,
                "asset_id": "NYXT",
            },
            token=token,
        )
        self.assertEqual(status, 200)
        status, _ = self._post(
            "/wallet/v1/transfer",
            {
                "seed": 7,
                "run_id": "activity-transfer",
                "payload": {"from_address": wallet_address, "to_address": "wallet-b", "amount": 5, "asset_id": "NYXT"},
            },
            token=token,
        )
        self.assertEqual(status, 200)
        status, payload = self._get("/portal/v1/activity?limit=50", token=token)
        self.assertEqual(status, 200)
        receipts = payload.get("receipts")
        self.assertTrue(isinstance(receipts, list) and receipts)


if __name__ == "__main__":
    unittest.main()
