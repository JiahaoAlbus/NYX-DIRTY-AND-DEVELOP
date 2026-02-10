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


class ServerWalletV1FaucetTests(unittest.TestCase):
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

    def _auth_token(self) -> tuple[str, str, str]:
        key = b"portal-key-0003-0003-0003-0003"
        pubkey = base64.b64encode(key).decode("utf-8")
        status, created = self._post("/portal/v1/accounts", {"handle": "carl", "pubkey": pubkey})
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

    def test_faucet_requires_auth_and_fee(self) -> None:
        status, _ = self._post("/wallet/v1/faucet", {"seed": 1, "run_id": "x", "address": "a", "amount": 10})
        self.assertEqual(status, 401)

        _, wallet_address, token = self._auth_token()
        status, result = self._post(
            "/wallet/v1/faucet",
            {"seed": 123, "run_id": "run-faucet-1", "address": wallet_address, "amount": 10, "asset_id": "NYXT"},
            token=token,
        )
        self.assertEqual(status, 200)
        self.assertGreater(result.get("fee_total", 0), 0)
        self.assertEqual(result.get("treasury_address"), "testnet-fee-address")


if __name__ == "__main__":
    unittest.main()
