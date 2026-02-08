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


class ServerChatV1Tests(unittest.TestCase):
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

    def _auth_token(self) -> str:
        key = b"portal-key-0002-0002-0002-0002"
        pubkey = base64.b64encode(key).decode("utf-8")
        status, created = self._post("/portal/v1/accounts", {"handle": "bob", "pubkey": pubkey})
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
        return verified.get("access_token")

    def test_chat_room_and_message(self) -> None:
        token = self._auth_token()
        status, room = self._post("/chat/v1/rooms", {"name": "General"}, token=token)
        self.assertEqual(status, 200)
        room_id = room.get("room_id")
        status, message = self._post(
            f"/chat/v1/rooms/{room_id}/messages",
            {"body": json.dumps({"ciphertext": "abc123", "iv": "def456"})},
            token=token,
        )
        self.assertEqual(status, 200)
        self.assertIn("receipt", message)
        status, listing = self._get(f"/chat/v1/rooms/{room_id}/messages", token=token)
        self.assertEqual(status, 200)
        self.assertTrue(listing.get("messages"))


if __name__ == "__main__":
    unittest.main()
