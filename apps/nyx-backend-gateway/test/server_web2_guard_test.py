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
from unittest.mock import patch

import nyx_backend_gateway.gateway as gateway
import nyx_backend_gateway.server as server
import nyx_backend_gateway.web2_guard as web2_guard


class ServerWeb2GuardTests(unittest.TestCase):
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

    def _auth_token(self) -> tuple[str, str]:
        key = b"portal-key-web2-guard-0001"
        pubkey = base64.b64encode(key).decode("utf-8")
        status, created = self._post("/portal/v1/accounts", {"handle": "web2user", "pubkey": pubkey})
        self.assertEqual(status, 200)
        account_id = created.get("account_id")

        status, challenge = self._post("/portal/v1/auth/challenge", {"account_id": account_id})
        self.assertEqual(status, 200)
        nonce = challenge.get("nonce")
        signature = base64.b64encode(hmac.new(key, nonce.encode("utf-8"), "sha256").digest()).decode("utf-8")
        status, verified = self._post(
            "/portal/v1/auth/verify",
            {"account_id": account_id, "nonce": nonce, "signature": signature},
        )
        self.assertEqual(status, 200)
        return account_id, verified.get("access_token")

    def test_web2_guard_request_flow(self) -> None:
        account_id, token = self._auth_token()

        status, _ = self._post(
            "/wallet/v1/faucet",
            {"seed": 123, "run_id": "run-web2-faucet", "payload": {"address": account_id, "amount": 1000}},
            token=token,
        )
        self.assertEqual(status, 200)

        status, allow = self._get("/web2/v1/allowlist")
        self.assertEqual(status, 200)
        self.assertTrue(isinstance(allow.get("allowlist"), list))

        with patch.object(web2_guard, "_web2_resolve_public_host", return_value=None), patch.object(
            web2_guard, "_web2_request", return_value=(200, b'{"ok":true}', False, None)
        ):
            status, resp = self._post(
                "/web2/v1/request",
                {"seed": 123, "run_id": "run-web2-1", "payload": {"url": "https://api.github.com/zen", "method": "GET"}},
                token=token,
            )
        self.assertEqual(status, 200)
        self.assertEqual(resp.get("response_status"), 200)
        self.assertTrue(resp.get("request_hash"))
        self.assertTrue(resp.get("response_hash"))
        self.assertGreater(resp.get("fee_total", 0), 0)

        status, listing = self._get("/web2/v1/requests?limit=10&offset=0", token=token)
        self.assertEqual(status, 200)
        self.assertEqual(len(listing.get("requests", [])), 1)


if __name__ == "__main__":
    unittest.main()
