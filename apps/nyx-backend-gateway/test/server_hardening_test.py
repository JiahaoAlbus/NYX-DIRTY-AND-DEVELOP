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

    def _auth_token(self) -> str:
        key = b"portal-key-hardening-0001"
        pubkey = base64.b64encode(key).decode("utf-8")
        conn = HTTPConnection("127.0.0.1", self.port, timeout=10)
        conn.request(
            "POST",
            "/portal/v1/accounts",
            body=json.dumps({"handle": "hardener", "pubkey": pubkey}, separators=(",", ":")),
            headers={"Content-Type": "application/json"},
        )
        created = json.loads(conn.getresponse().read().decode("utf-8"))
        account_id = created.get("account_id")
        conn.close()

        conn = HTTPConnection("127.0.0.1", self.port, timeout=10)
        conn.request(
            "POST",
            "/portal/v1/auth/challenge",
            body=json.dumps({"account_id": account_id}, separators=(",", ":")),
            headers={"Content-Type": "application/json"},
        )
        challenge = json.loads(conn.getresponse().read().decode("utf-8"))
        nonce = challenge.get("nonce")
        conn.close()

        signature = base64.b64encode(hmac.new(key, nonce.encode("utf-8"), "sha256").digest()).decode("utf-8")
        conn = HTTPConnection("127.0.0.1", self.port, timeout=10)
        conn.request(
            "POST",
            "/portal/v1/auth/verify",
            body=json.dumps({"account_id": account_id, "nonce": nonce, "signature": signature}, separators=(",", ":")),
            headers={"Content-Type": "application/json"},
        )
        verified = json.loads(conn.getresponse().read().decode("utf-8"))
        conn.close()
        return verified.get("access_token")

    def test_invalid_run_id_rejected(self) -> None:
        token = self._auth_token()
        conn = HTTPConnection("127.0.0.1", self.port, timeout=10)
        payload = {
            "seed": 123,
            "run_id": "../bad",
            "module": "exchange",
            "action": "route_swap",
            "payload": {"asset_in": "asset-a", "asset_out": "asset-b", "amount": 5, "min_out": 3},
        }
        body = json.dumps(payload, separators=(",", ":"))
        conn.request(
            "POST",
            "/run",
            body=body,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
        )
        response = conn.getresponse()
        response.read()
        self.assertEqual(response.status, 400)
        conn.close()

    def test_message_too_long_rejected(self) -> None:
        token = self._auth_token()
        conn = HTTPConnection("127.0.0.1", self.port, timeout=10)
        payload = {
            "seed": 123,
            "run_id": "run-chat-long",
            "payload": {
                "channel": "dm/acct-hardener/acct-peer",
                "message": json.dumps({"ciphertext": "x" * 3000, "iv": "BB=="}),
            },
        }
        body = json.dumps(payload, separators=(",", ":"))
        conn.request(
            "POST",
            "/chat/send",
            body=body,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
        )
        response = conn.getresponse()
        response.read()
        self.assertEqual(response.status, 400)
        conn.close()

    def test_payload_too_large_rejected(self) -> None:
        token = self._auth_token()
        conn = HTTPConnection("127.0.0.1", self.port, timeout=10)
        payload = {
            "seed": 1,
            "run_id": "run-large",
            "module": "exchange",
            "action": "route_swap",
            "payload": {"text": "y" * 6000},
        }
        body = json.dumps(payload, separators=(",", ":"))
        conn.request(
            "POST",
            "/run",
            body=body,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
        )
        response = conn.getresponse()
        response.read()
        self.assertEqual(response.status, 400)
        conn.close()


if __name__ == "__main__":
    unittest.main()
