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


class ServerWalletV1AirdropTests(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["NYX_TESTNET_FEE_ADDRESS"] = "testnet-fee-address"
        os.environ.pop("NYX_TESTNET_TREASURY_ADDRESS", None)
        os.environ["NYX_FAUCET_COOLDOWN_SECONDS"] = "0"
        os.environ["NYX_FAUCET_MAX_CLAIMS_PER_24H"] = "10"
        os.environ["NYX_FAUCET_MAX_AMOUNT_PER_24H"] = "100000"
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

    def _auth_token(self, handle: str, key: bytes) -> tuple[str, str, str]:
        pubkey = base64.b64encode(key).decode("utf-8")
        status, created = self._post("/portal/v1/accounts", {"handle": handle, "pubkey": pubkey})
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

    def test_airdrop_tasks_and_claim(self) -> None:
        status, _ = self._get("/wallet/v1/airdrop/tasks")
        self.assertEqual(status, 401)

        a_id, a_wallet, a_token = self._auth_token("airdrop_a", b"airdrop-key-a-0001-0001-0001")
        b_id, b_wallet, b_token = self._auth_token("airdrop_b", b"airdrop-key-b-0002-0002-0002")

        # Fund accounts for fees and actions
        status, _ = self._post(
            "/wallet/v1/faucet",
            {"seed": 1, "run_id": "a-nyxt", "address": a_wallet, "amount": 3000, "asset_id": "NYXT"},
            token=a_token,
        )
        self.assertEqual(status, 200)
        status, _ = self._post(
            "/wallet/v1/faucet",
            {"seed": 2, "run_id": "b-nyxt", "address": b_wallet, "amount": 3000, "asset_id": "NYXT"},
            token=b_token,
        )
        self.assertEqual(status, 200)
        status, _ = self._post(
            "/wallet/v1/faucet",
            {"seed": 3, "run_id": "b-echo", "address": b_wallet, "amount": 50, "asset_id": "ECHO"},
            token=b_token,
        )
        self.assertEqual(status, 200)

        # Store task: publish listing (A) then purchase (B)
        status, _ = self._post(
            "/run",
            {
                "seed": 10,
                "run_id": "listing-1",
                "module": "marketplace",
                "action": "listing_publish",
                "payload": {"publisher_id": a_wallet, "sku": "sku-1", "title": "Test Item", "price": 5},
            },
            token=a_token,
        )
        self.assertEqual(status, 200)
        status, listings = self._get("/marketplace/listings?limit=10&offset=0")
        self.assertEqual(status, 200)
        listing_id = listings.get("listings", [])[0].get("listing_id")
        self.assertTrue(listing_id)
        status, _ = self._post(
            "/run",
            {
                "seed": 11,
                "run_id": "purchase-1",
                "module": "marketplace",
                "action": "purchase_listing",
                "payload": {"buyer_id": b_wallet, "listing_id": listing_id, "qty": 1},
            },
            token=b_token,
        )
        self.assertEqual(status, 200)

        # Chat task: send E2EE DM (B)
        status, _ = self._post(
            "/run",
            {
                "seed": 12,
                "run_id": "chat-1",
                "module": "chat",
                "action": "message_event",
                "payload": {"channel": f"dm/{a_id}/{b_id}", "message": json.dumps({"ciphertext": "x", "iv": "y"})},
            },
            token=b_token,
        )
        self.assertEqual(status, 200)

        # Trade task: A buys, B sells (NYXT/ECHO)
        status, _ = self._post(
            "/run",
            {
                "seed": 20,
                "run_id": "a-buy-1",
                "module": "exchange",
                "action": "place_order",
                "payload": {
                    "owner_address": a_wallet,
                    "side": "BUY",
                    "asset_in": "NYXT",
                    "asset_out": "ECHO",
                    "amount": 10,
                    "price": 1,
                },
            },
            token=a_token,
        )
        self.assertEqual(status, 200)
        status, _ = self._post(
            "/run",
            {
                "seed": 21,
                "run_id": "b-sell-1",
                "module": "exchange",
                "action": "place_order",
                "payload": {
                    "owner_address": b_wallet,
                    "side": "SELL",
                    "asset_in": "ECHO",
                    "asset_out": "NYXT",
                    "amount": 10,
                    "price": 1,
                },
            },
            token=b_token,
        )
        self.assertEqual(status, 200)

        status, tasks = self._get("/wallet/v1/airdrop/tasks", token=b_token)
        self.assertEqual(status, 200)
        task_rows = {t["task_id"]: t for t in tasks.get("tasks", [])}
        self.assertTrue(task_rows["store_1"]["completed"])
        self.assertTrue(task_rows["chat_1"]["completed"])
        self.assertTrue(task_rows["trade_1"]["completed"])

        # Claim store task and ensure it cannot be claimed twice.
        status, claim = self._post(
            "/wallet/v1/airdrop/claim",
            {"seed": 30, "run_id": "airdrop-claim-store", "task_id": "store_1"},
            token=b_token,
        )
        self.assertEqual(status, 200)
        self.assertEqual(claim.get("task_id"), "store_1")
        self.assertGreater(int(claim.get("reward", 0) or 0), 0)
        status, again = self._post(
            "/wallet/v1/airdrop/claim",
            {"seed": 31, "run_id": "airdrop-claim-store-2", "task_id": "store_1"},
            token=b_token,
        )
        self.assertEqual(status, 409)
        self.assertIn("error", again)


if __name__ == "__main__":
    unittest.main()
