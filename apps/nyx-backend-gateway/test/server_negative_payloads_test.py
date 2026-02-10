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


class ServerNegativePayloadTests(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["NYX_TESTNET_FEE_ADDRESS"] = "testnet-fee-address"
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

    def _post_raw(self, path: str, body: str, token: str | None = None) -> tuple[int, dict]:
        conn = HTTPConnection("127.0.0.1", self.port, timeout=10)
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        conn.request("POST", path, body=body, headers=headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()
        return response.status, json.loads(data.decode("utf-8"))

    def _post(self, path: str, payload: dict, token: str | None = None) -> tuple[int, dict]:
        return self._post_raw(path, json.dumps(payload, separators=(",", ":")), token=token)

    def _auth_token(self) -> tuple[str, str, str, bytes]:
        key = b"portal-neg-0001-"
        pubkey = base64.b64encode(key).decode("utf-8")
        status, created = self._post("/portal/v1/accounts", {"handle": "neguser", "pubkey": pubkey})
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
        return account_id, wallet_address, verified.get("access_token"), key

    def test_invalid_signature_rejected(self) -> None:
        account_id, _, _, _ = self._auth_token()
        status, challenge = self._post("/portal/v1/auth/challenge", {"account_id": account_id})
        self.assertEqual(status, 200)
        nonce = challenge.get("nonce")
        bad_signature = base64.b64encode(b"bad-signature").decode("utf-8")
        status, payload = self._post(
            "/portal/v1/auth/verify",
            {"account_id": account_id, "nonce": nonce, "signature": bad_signature},
        )
        self.assertEqual(status, 400)
        self.assertIn("error", payload)

    def test_malformed_json_rejected(self) -> None:
        _, _, token, _ = self._auth_token()
        status, payload = self._post_raw("/wallet/v1/faucet", "{bad-json", token=token)
        self.assertEqual(status, 400)
        self.assertIn("error", payload)

    def test_invalid_payload_rejected(self) -> None:
        _, wallet_address, token, _ = self._auth_token()
        status, _ = self._post(
            "/wallet/v1/faucet",
            {"seed": 123, "run_id": "neg-faucet", "payload": {"address": wallet_address, "amount": 100}},
            token=token,
        )
        self.assertEqual(status, 200)

        status, payload = self._post(
            "/wallet/v1/transfer",
            {"seed": 123, "run_id": "neg-transfer", "payload": {"from_address": wallet_address, "amount": -1}},
            token=token,
        )
        self.assertEqual(status, 400)
        self.assertIn("error", payload)

    def test_invalid_token_rejected(self) -> None:
        status, payload = self._post(
            "/wallet/v1/faucet",
            {"seed": 123, "run_id": "neg-token", "payload": {"address": "wallet-x", "amount": 10}},
            token="not-a-token",
        )
        self.assertEqual(status, 401)
        self.assertIn("error", payload)


if __name__ == "__main__":
    unittest.main()
